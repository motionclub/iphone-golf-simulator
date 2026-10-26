#import "UnityAppController.h"
#import "Unity/DisplayManager.h"
#import "Unity/UnityInterface.h"

// Unity-internal method implemented in its exported DisplayManager.mm.
@interface DisplayManager (SportsSceneRegistration)
- (void)registerScreen:(UIScreen*)screen;
@end

// Unity-internal method implemented in UnityAppController+Rendering.mm.
@interface UnityAppController (SportsRenderingRegistration)
- (void)callbackFramerateChange:(int)targetFPS;
@end

@interface SportsUnityAppController : UnityAppController
- (void)sportsDriveLoopFromScreen:(UIScreen*)screen;
@end

@interface SportsExternalRendererController : UIViewController
@end
@implementation SportsExternalRendererController
- (UIInterfaceOrientationMask)supportedInterfaceOrientations { return UIInterfaceOrientationMaskLandscape; }
@end

// Unity creates its secondary UIWindow with a raw subview and no controller.
// Give that same render surface a scene-owned controller before the host hides
// its waiting window. Never move the phone's primary surface to the TV.
// AirPlay compresses and streams whatever mode the TV screen is in, and Unity picks the
// preferred (largest) one: 4K on a 4K Apple TV. Four times the pixels to render, encode, send
// and decode, for a picture the player sits across the room from. Stream at 1080p at most.
static void SportsCapExternalMode(UIScreen *screen) {
    UIScreenMode *best = nil;
    for (UIScreenMode *mode in screen.availableModes) {
        CGSize size = mode.size;
        if (size.width > 1920 || size.height > 1080) continue;
        if (!best || size.width * size.height > best.size.width * best.size.height) best = mode;
    }
    if (!best || [screen.currentMode isEqual:best]) return;
    NSLog(@"[SportsDisplay] external mode %@ -> %@", NSStringFromCGSize(screen.currentMode.size), NSStringFromCGSize(best.size));
    screen.currentMode = best;
}

// Latency plan P1 (B4). Unity's maxQueuedFrames setting only reaches the phone's layer; the TV layer kept CAMetalLayer's
// default of three drawables, so a finished frame could wait two refreshes before it was shown. Two is the least Metal
// allows. Launch with `-sportsTVQueuedFrames 3` to compare on a device.
static void SportsCapExternalQueue(UIView *view) {
    if (![view.layer isKindOfClass:CAMetalLayer.class]) return;
    NSInteger frames = [NSUserDefaults.standardUserDefaults integerForKey:@"sportsTVQueuedFrames"];
    CAMetalLayer *layer = (CAMetalLayer*)view.layer;
    layer.maximumDrawableCount = frames == 3 ? 3 : 2;
    NSLog(@"[SportsDisplay] external queued frames %lu", (unsigned long)layer.maximumDrawableCount);
}

// Scene connection and Unity's UIScreen notification cache can arrive in either order.
// Build the display cache from live scenes, keeping the phone at zero, then initialize
// the exact external screen. Merely calling Display.Activate(1) on a stale cache leaves
// connection.window and connection.view nil and never produces a frame.
extern "C" __attribute__((visibility("default"))) int SportsPrepareExternalDisplay() {
    DisplayManager *manager = [DisplayManager Instance];
    if (!manager) return -1;
    UIWindowScene *externalScene = nil;
    void *screens[8];
    screens[0] = (__bridge void*)manager.mainDisplay.screen;
    int count = 1;
    for (UIScene *candidate in UIApplication.sharedApplication.connectedScenes) {
        if (![candidate isKindOfClass:UIWindowScene.class] ||
            ![candidate.session.role isEqualToString:UIWindowSceneSessionRoleExternalDisplayNonInteractive]) continue;
        UIWindowScene *scene = (UIWindowScene*)candidate;
        if (scene.activationState == UISceneActivationStateUnattached || scene.screen == manager.mainDisplay.screen) continue;
        if (!externalScene) externalScene = scene;
        if (count < 8) { [manager registerScreen:scene.screen]; screens[count++] = (__bridge void*)scene.screen; }
    }
    if (!externalScene) return -1;
    SportsCapExternalMode(externalScene.screen);
    UnityUpdateDisplayListCache(screens, count);
    UnityActivateScreenForRendering((__bridge void*)externalScene.screen);
    DisplayConnection *connection = manager[externalScene.screen];
    UIWindow *window = connection.window;
    UIView *view = connection.view;
    if (!window || !view || connection == manager.mainDisplay) return -1;
    window.windowScene = externalScene;
    window.frame = externalScene.coordinateSpace.bounds;
    if (!window.rootViewController) {
        SportsExternalRendererController *controller = [SportsExternalRendererController new];
        [view removeFromSuperview];
        controller.view = view;
        window.rootViewController = controller;
    }
    view.frame = window.bounds;
    view.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    window.hidden = NO;
    [window layoutIfNeeded];
    SportsCapExternalQueue(view);
    // Experiment (P1, B4), off unless launched with `-sportsTVClock YES`: pace the game loop by the TV's refresh, not the phone's.
    if ([NSUserDefaults.standardUserDefaults boolForKey:@"sportsTVClock"])
        [(SportsUnityAppController*)GetAppController() sportsDriveLoopFromScreen:externalScene.screen];
    NSLog(@"[SportsDisplay] external ready index=1 screen=%@ window=%@ view=%@ scene=%@ bounds=%@", externalScene.screen, window, view, window.windowScene, NSStringFromCGRect(window.bounds));
    return window.windowScene == externalScene && !window.hidden ? 1 : -1;
}

// Unity's default picker accepts any foreground scene, including the TV scene.
// DisplayManager still treats the phone as display 0, so always initialize there.
extern "C" void SportsRegisterPointCapture();
extern "C" id SportsMakePointRenderDelegate(id existing);
@implementation SportsUnityAppController
- (void)preStartUnity { [super preStartUnity]; SportsRegisterPointCapture(); }
- (void)shouldAttachRenderDelegate {
    [super shouldAttachRenderDelegate];
    self.renderDelegate=SportsMakePointRenderDelegate(self.renderDelegate);
}
- (UIWindowScene*)pickStartupWindowScene:(NSSet<UIScene*>*)scenes {
    for (UIScene *scene in scenes) {
        if ([scene isKindOfClass:UIWindowScene.class] &&
            [scene.session.role isEqualToString:UIWindowSceneSessionRoleApplication]) {
            NSLog(@"[SportsDisplay] Unity primary renderer assigned to phone scene");
            return (UIWindowScene*)scene;
        }
    }
    return nil;
}
- (BOOL)shouldUseMetalDisplayLink { return NO; }

// The game loop is driven by the phone's display link, so frames reach the TV on the phone's clock: up to a frame of
// jitter on top of everything else. This swaps in the TV screen's own link (nil: back to the phone's, as Unity made it),
// and goes back by itself if the TV goes away, so the loop never waits on a screen that is gone.
- (void)sportsDriveLoopFromScreen:(UIScreen*)screen {
    CADisplayLink *link = screen ? [screen displayLinkWithTarget:self selector:@selector(repaintDisplayLink)]
                                 : [CADisplayLink displayLinkWithTarget:self selector:@selector(repaintDisplayLink)];
    if (!link || !_displayLink) return;
    link.paused = _displayLink.paused;
    [_displayLink invalidate];
    _displayLink = link;
    [self callbackFramerateChange:-1];
    [_displayLink addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
    NSLog(@"[SportsDisplay] game loop clock: %@", screen ? @"TV" : @"phone");
    static id sceneGone;
    if (sceneGone) { [NSNotificationCenter.defaultCenter removeObserver:sceneGone]; sceneGone = nil; }
    if (!screen) return;
    // Any TV scene going away counts: by then its `screen` may already be gone too.
    __weak SportsUnityAppController *weakSelf = self;
    sceneGone = [NSNotificationCenter.defaultCenter addObserverForName:UISceneDidDisconnectNotification object:nil
        queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *note) {
            UIScene *scene = note.object;
            if (![scene.session.role isEqualToString:UIWindowSceneSessionRoleExternalDisplayNonInteractive]) return;
            [weakSelf sportsDriveLoopFromScreen:nil];
        }];
}
@end
IMPL_APP_CONTROLLER_SUBCLASS(SportsUnityAppController)
