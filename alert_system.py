import os
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

class AlertSystem:
    def __init__(self):
        load_dotenv()
        
        # Twilio credentials (you'll need to set these up)
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        self.alert_phone = os.getenv('ALERT_PHONE_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.twilio_enabled = True
        else:
            self.twilio_enabled = False
            print("⚠️  Twilio credentials not found. SMS alerts disabled.")
            print("   Alerts will be simulated in console.")
    
    def send_sms_alert(self, message):
        """Send SMS alert using Twilio"""
        if not self.twilio_enabled:
            return self.simulate_alert(message)
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.alert_phone
            )
            print(f"✅ SMS Alert sent! SID: {message.sid}")
            return True
        except Exception as e:
            print(f"❌ Error sending SMS: {str(e)}")
            return False
    
    def simulate_alert(self, message):
        """Simulate alert when Twilio is not configured"""
        print("\n" + "="*60)
        print("📱 SIMULATED MOBILE ALERT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Message: {message}")
        print("="*60 + "\n")
        return True
    
    def send_fall_alert(self, fall_event):
        """Send fall detection alert"""
        timestamp = fall_event.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        confidence = fall_event.get('confidence', 0)
        
        message = f"""
🚨 FALL DETECTED! 🚨

Time: {timestamp}
Confidence: {confidence:.1f}%

Immediate assistance may be required.
Please check on the person immediately.
        """.strip()
        
        return self.send_sms_alert(message)
    
    def test_alert(self):
        """Test the alert system"""
        test_message = "🧪 Test Alert - Fall Detection System is working!"
        print("Sending test alert...")
        return self.send_sms_alert(test_message)


# Standalone function for quick testing
def test_alert_system():
    """Quick test of alert system"""
    alert_system = AlertSystem()
    alert_system.test_alert()


if __name__ == "__main__":
    test_alert_system()