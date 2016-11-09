require 'houston'
require 'json'
require 'optparse'

APN = Houston::Client.production
APN.certificate = File.read("apns-dev-cert.pem")

# An example of the token sent back when a device registers for notifications
token = "<8ff95005 933719c0 cffb591f f58c1c2d 75668993 133d2b90 e0e8581b ba9addca>"

# Create a notification that alerts a message to the user, plays a sound, and sets the badge on the app
notification = Houston::Notification.new(device: token)
notification.alert = "Hello, World!"

# Notifications can also change the badge count, have a custom sound, have a category identifier, indicate available Newsstand content, or pass along arbitrary data.
notification.badge = 57
notification.sound = "sosumi.aiff"
notification.category = "INVITE_CATEGORY"
notification.content_available = true
notification.custom_data = {foo: "bar"}

# And... sent! That's all it takes.
APN.push(notification)
puts notification.error
