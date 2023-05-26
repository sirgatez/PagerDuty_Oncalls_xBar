#!/usr/bin/env zsh
# <bitbar.title>PagerDuty Alerts</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Joshua Briefman</bitbar.author>
# <bitbar.author.github>sirgatez</bitbar.author.github>
# <bitbar.desc>Widget PagerDuty alerts.</bitbar.desc>
# <bitbar.dependencies>bash/zsh and Python 3</bitbar.dependencies>
# <bitbar.image>N/A</bitbar.image>
# <bitbar.abouturl>https://github.com/sirgatez/PagerDuty_Oncalls_xBar</bitbar.abouturl>

# This wrapper is needed to execute Python scripts because the default path
# on MacOS does NOT include paths added in profile, or .zshrc files.

# Configure these two scripts for your environment.
folder="PythonScripts"
script="PagerDuty_Oncalls.py"

# For SwuftBar you must cd into your Plugin folder to access anything within it.
# BitBar and xBar default to executing the script from the script's folder.
cd ${HOME}/.dotfiles/home/9682975F-1BF2-4826-BAAF-E9478E1BB3F4/SwiftBarPlugins/Enabled

# Code begins here.
error_msg=""
if [[ -d ${folder} ]]; then
	cd ${folder}
	if [[ -f ${script} ]]; then
		# Add Homebrew ARM64 and AMD64 paths ahead of systme incase installed.
		export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"
		# Capture output incase something goes wrong, we can return a readable error in xBar.
		output="$(./${script})"
		if [[ $? == 0 ]]; then
			echo "${output}"
			exit 0
		else
			error_msg="Failed to execute script successfully ${script}."
		fi
	else
		error_msg="Failed to find script ${script}."
	fi
else
	error_msg="Failed to find folder ${folder}."
fi

echo "☠️"
echo "---"
echo "${error_msg}"
