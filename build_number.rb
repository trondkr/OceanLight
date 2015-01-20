#!/usr/bin/env ruby

# Giants' Shoulders Trodden Upon
# Based on the xcode auto-versioning script for Subversion by Axel Andersson
# Updated for git by Marcus S. Zarra and Matt Long
# Converted to ruby by Abizer Nasir

# Improved? By Jonathan Zhan

# Appends the number of commits on the current branch and a short git hash to the version number set in Xcode.
# Writes this information to CFBundleVersion in your Apps info.plist

# How to use:
# Xcode > Product > Edit Schemes
# Pick a Scheme (I use Archive, so it only gets updatethis when doing new distribution builds)
# Add a run script to pre-actions for your chosen scheme
# Set your shell to "/usr/bin/env ruby" and get build settings from your target of choice
# You're done!

######################################################

# These are the common places where git is installed.
# Change this if your path isn't here

common_git_paths = %w[/usr/bin/git /usr/local/git/bin/git /opt/local/bin/git]
git_path = ""

common_git_paths.each do |p|
if File.exist?(p)
git_path = p
break
end
end

if git_path == ""
puts "Path to git not found"
exit
end

sourceRoot = ENV['PROJECT_DIR']

Dir.chdir(sourceRoot){
	command_line = git_path + " rev-parse --short HEAD"
	sha = `#{command_line}`.chomp #short git hash
	ver = `git describe`
	revRaw = `git rev-list --all | wc -l`.chomp #total number of commits
	rev = "r" + revRaw.gsub(/\s+/,"") # last git tag

	info_file = ENV['SRCROOT'].gsub(/ /){"\\ "} + "/" + ENV['INFOPLIST_FILE'].gsub(/ /){"\\ "}

	`/usr/libexec/PlistBuddy -c "Set :CFBundleVersion #{rev+'/'+sha}" #{info_file}`
    `/usr/libexec/PlistBuddy -c "Set :CFBundleVersion #{rev+'/'+sha}" #{ENV['INFOPLIST_PATH']}`
}
