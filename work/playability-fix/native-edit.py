from pathlib import Path
import json,shutil
r=Path.cwd(); f=r/'Unity/Assets/Plugins/iOS/SportsUnityAppController.mm'; b=r/'work/playability-fix/before/Unity/Assets/Plugins/iOS/SportsUnityAppController.mm'; b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,b)
s=f.read_text();s=s.replace('#import "Unity/DisplayManager.h"','#import "Unity/DisplayManager.h"\n#import "Unity/UnityInterface.h"\n\n// Unity-internal method implemented in its exported DisplayManager.mm.\n@interface DisplayManager (SportsSceneRegistration)\n- (void)registerScreen:(UIScreen*)screen;\n@end')
a=s.index('extern "C" __attribute__((visibility("default"))) bool SportsPresentExternalDisplay()');e=s.index('// Unity\'s default picker',a)
s=s[:a]+'''// Scene connection and Unity's UIScreen notification cache can arrive in either order.
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
    NSLog(@"[SportsDisplay] external ready index=1 screen=%@ window=%@ view=%@ scene=%@ bounds=%@", externalScene.screen, window, view, window.windowScene, NSStringFromCGRect(window.bounds));
    return window.windowScene == externalScene && !window.hidden ? 1 : -1;
}

'''+s[e:];f.write_text(s)
j=r/'work/playability-fix/changes.json';paths=json.loads(j.read_text());paths.append(str(f.relative_to(r)))
# Make current settings descriptions and primary action match the tutorial-free routes.
p=r/'GolfArcade/Unity/IslandScreens.swift';bp=r/'work/playability-fix/before/GolfArcade/Unity/IslandScreens.swift';bp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,bp)
s=p.read_text().replace('sport == .golf ? id == "round" : id == "tutorial" && !m.done','sport == .golf ? id == "round" : id == "exhibition"').replace('Erase tutorials & campaign','Reset campaign').replace('Starts the tutorial and the Island Circuit from the beginning.','Starts the Island Circuit from the beginning.');p.write_text(s);paths.append(str(p.relative_to(r)))
j.write_text(json.dumps(paths,indent=2))
for path in paths:
 src=r/path; dst=r/'work/golf-look/device/combined/Source'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
