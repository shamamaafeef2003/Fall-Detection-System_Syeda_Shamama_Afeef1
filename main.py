import sys
import os
from fall_detector import FallDetector
from alert_system import AlertSystem

def main():
    print("="*60)
    print("Fall Detection System - Proof of Concept")
    print("="*60)
    
    # Initialize systems
    detector = FallDetector()
    alert_system = AlertSystem()
    
    # Get video path from command line or use default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("Enter video path (or press Enter for 'videos/test_fall.mp4'): ").strip()
        if not video_path:
            video_path = "videos/test_fall.mp4"
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found: {video_path}")
        print("\nPlease provide a valid video path.")
        return
    
    # Set output path
    output_path = "output/detected_falls.mp4"
    os.makedirs("output", exist_ok=True)
    
    print(f"\n📹 Analyzing video: {video_path}")
    print(f"💾 Output will be saved to: {output_path}\n")
    
    # Process video
    results = detector.process_video(video_path, output_path)
    
    if results:
        # Display results
        print("\n" + "="*60)
        print("DETECTION RESULTS")
        print("="*60)
        print(f"Total frames processed: {results['total_frames']}")
        print(f"Video FPS: {results['fps']}")
        print(f"Total falls detected: {results['total_falls']}")
        
        if results['fall_events']:
            print("\nFall Events:")
            for i, event in enumerate(results['fall_events'], 1):
                print(f"\n  Event {i}:")
                print(f"    - Timestamp: {event['timestamp']:.2f}s (frame {event['frame']})")
                print(f"    - Confidence: {event['confidence']:.1f}%")
                print(f"    - DateTime: {event['datetime']}")
            
            # Send alert for first fall detected
            print("\n" + "="*60)
            print("SENDING ALERT")
            print("="*60)
            alert_system.send_fall_alert(results['fall_events'][0])
        else:
            print("\n✅ No falls detected in the video.")
        
        # Save results
        detector.save_results(results)
        
        # Calculate accuracy metrics
        print("\n" + "="*60)
        print("ACCURACY METRICS")
        print("="*60)
        if results['fall_events']:
            avg_confidence = sum(e['confidence'] for e in results['fall_events']) / len(results['fall_events'])
            print(f"Average Detection Confidence: {avg_confidence:.1f}%")
            print(f"Detection Rate: {len(results['fall_events'])} falls detected")
            print(f"False Positive Rate: N/A (requires labeled ground truth)")
        else:
            print("No falls detected - accuracy cannot be calculated")
        
        print("\n✅ Processing complete!")
        print(f"📁 Annotated video saved to: {output_path}")
        print(f"📊 Results saved to: output/detection_results.json")
    else:
        print("❌ Error processing video")


if __name__ == "__main__":
    main()