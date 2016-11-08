require 'houston'
require 'json'
require 'optparse'

options = {}
parser = OptionParser.new do |opts|
  opts.banner = "\nPush Noitification script.\n"

  opts.on("-p n", "--port", "Provide the port") do |p|
    puts p
    options[:port] = p
  end

  opts.on("-j n", "--json", "Path to JSON file with tokens") do |j|
    puts j
    options[:json] = j
  end

  opts.on("-h", "--help", "Displays help") do
    puts opts
    exit
  end
end

parser.parse!(ARGV)

puts options
if options[:json].nil?
  puts "Fatal Error: Must provide json path"
  abort
end

puts "Sending push notification"

tokensFile = File.read(options[:json])
tokens_hash = JSON.parse(tokensFile)
tokens = tokens_hash['deviceTokens']

configFile = File.read("config.json")
config_hash = JSON.parse(configFile)
pemFile = config_hash['pemFile']

# Environment variables are automatically read, or can be overridden by any specified options. You can also
# conveniently use `Houston::Client.development` or `Houston::Client.production`.
APN = Houston::Client.development
APN.certificate = File.read(pemFile)

for token in tokens

  # Create a notification that alerts a message to the user, plays a sound, and sets the badge on the app
  notification = Houston::Notification.new(device: token)
  notification.alert = "You have been invited to a game"

  # Notifications can also change the badge count, have a custom sound, have a category identifier, indicate available Newsstand content, or pass along arbitrary data.
  notification.badge = 0
  notification.sound = "default"
  notification.category = "INVITE_CATEGORY"
  notification.content_available = true
  notification.custom_data = {port: options[:port]}

  # And... sent! That's all it takes.
  APN.push(notification)

end
