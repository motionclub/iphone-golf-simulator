    // Isolated cloth proof export only: capture one warmed two-hero GPU workload.
    if (getenv("CLOTH_GPU_CAPTURE")) {
        [UIApplication sharedApplication].idleTimerDisabled = YES;
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_SEC), dispatch_get_main_queue(), ^{
            MTLCaptureManager *manager = [MTLCaptureManager sharedCaptureManager];
            MTLCaptureDescriptor *descriptor = [[MTLCaptureDescriptor alloc] init];
            descriptor.captureObject = MTLCreateSystemDefaultDevice();
            descriptor.destination = MTLCaptureDestinationGPUTraceDocument;
            NSString *documents = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
            descriptor.outputURL = [NSURL fileURLWithPath:[documents stringByAppendingPathComponent:@"cloth_final.gputrace"]];
            [[NSFileManager defaultManager] removeItemAtURL:descriptor.outputURL error:nil];
            NSError *error = nil;
            NSString *statusPath = [documents stringByAppendingPathComponent:@"cloth_capture_status.txt"];
            [@"timer reached" writeToFile:statusPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
            if ([manager startCaptureWithDescriptor:descriptor error:&error]) {
                [@"capture started" writeToFile:statusPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
                fprintf(stderr,"CLOTH_GPU_CAPTURE_STARTED\n");
                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 120 * NSEC_PER_MSEC), dispatch_get_main_queue(), ^{
                    [manager stopCapture];
                    [@"capture complete" writeToFile:statusPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
                    fprintf(stderr,"CLOTH_GPU_CAPTURE_COMPLETE\n");
                });
            } else { [[error description] writeToFile:statusPath atomically:YES encoding:NSUTF8StringEncoding error:nil]; fprintf(stderr,"CLOTH_GPU_CAPTURE_FAILED %s\n", [[error description] UTF8String]); }
        });
    }

