require 'houston'
require 'json'
require 'optparse'

APN = Houston::Client.production
APN.certificate = File.read("apns-dev-cert.pem")

# An example of the token sent back when a device registers for notifications
token = "<54c9e7f8 1d5e79e5 9cd1bdc8 342a90f6 c176bd7d 2f00e826 190406f5 725891b8>"

# Create a notification that alerts a message to the user, plays a sound, and sets the badge on the app
notification = Houston::Notification.new(device: token)
notification.alert = "Hello, World!"

# Notifications can also change the badge count, have a custom sound, have a category identifier, indicate available Newsstand content, or pass along arbitrary data.
notification.badge = 0
notification.sound = "sosumi.aiff"
notification.category = "INVITE_CATEGORY"
notification.content_available = true
notification.custom_data = {foo: "bar"}

# And... sent! That's all it takes.
APN.push(notification)
puts notification.error
