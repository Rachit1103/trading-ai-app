from pyngrok import ngrok
import time

# Kill any existing ngrok tunnels
ngrok.kill()

# Create ngrok tunnel
public_tunnel = ngrok.connect(8500, "http")

print("🌐 PUBLIC URL CREATED!")
print("=" * 50)
print(f"Your Trading AI App is now live at:")
print(f"📱 {public_tunnel}")
print("=" * 50)
print("Share this URL with anyone!")
print("Works on mobile, desktop, and tablets")
print("=" * 50)

# Keep tunnel alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopping ngrok tunnel...")
    ngrok.kill()
    print("✅ Tunnel closed")
