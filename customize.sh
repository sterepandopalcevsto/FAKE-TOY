##########################################################################################
#
# Battery Optimizer Magisk Module Config Script
#
##########################################################################################

##########################################################################################
# Config Flags
##########################################################################################

# Minimum Android version supported is 5.0 (Lollipop)
MINAPI=21
# Debug mode for verbose logs
DEBUG=true

##########################################################################################
# Replace list
##########################################################################################

# We don't need to replace any system files
REPLACE=""

##########################################################################################
# Permissions
##########################################################################################

set_permissions() {
  # Set permissions for our scripts
  set_perm $MODPATH/service.sh 0 0 0755
  set_perm $MODPATH/post-fs-data.sh 0 0 0755
  
  # Create an empty log file with proper permissions
  touch $MODPATH/battery_optimizer.log
  set_perm $MODPATH/battery_optimizer.log 0 0 0644
}

##########################################################################################
# Custom Functions
##########################################################################################

# Function to check device compatibility
check_compatibility() {
  ui_print "- Checking device compatibility..."
  
  # Check Android version
  if [ $API -lt $MINAPI ]; then
    ui_print "! Unsupported Android version: $API"
    ui_print "! Minimum required API: $MINAPI"
    abort "! Aborting installation"
  fi
  
  # Check if root is available (should be satisfied by Magisk already)
  if ! command -v su > /dev/null; then
    ui_print "! Root access not available"
    abort "! Aborting installation"
  fi
  
  ui_print "- Device is compatible"
}

# Function to create configuration files
create_configs() {
  ui_print "- Creating configuration files..."
  
  # Create main configuration file
  cat << EOF > $MODPATH/config.conf
# Battery Optimizer Configuration
# You can edit this file to customize the behavior

# CPU Governor (conservative/powersave/ondemand/performance)
CPU_GOVERNOR=conservative

# Maximum CPU Frequency Reduction (percentage)
MAX_FREQ_REDUCTION=10

# Aggressive Doze Mode (true/false)
AGGRESSIVE_DOZE=true

# Manage Battery Hungry Apps (true/false)
MANAGE_APPS=true

# Network Optimization (true/false)
NETWORK_OPTIMIZATION=true

# Advanced I/O Tweaks (true/false)
IO_TWEAKS=true

# VM Memory Tweaks (true/false)
VM_TWEAKS=true

# Debug Logging (true/false)
DEBUG_LOG=true
EOF

  ui_print "- Configuration created at: $MODPATH/config.conf"
}

##########################################################################################
# Main Installation
##########################################################################################

# Print welcome message
ui_print "**************************************"
ui_print "*        Battery Optimizer           *"
ui_print "*        Version: $(grep_prop version $MODPATH/module.prop)        *"
ui_print "**************************************"

# Check device compatibility
check_compatibility

# Create configuration files
create_configs

# Inform user about tuning
ui_print "- The module will activate after reboot"
ui_print "- Battery optimizations will be applied automatically"
ui_print "- You can edit $MODPATH/config.conf for customization"
ui_print "- Check $MODPATH/battery_optimizer.log for details"

# Continue with MMT Extended Logic
SKIPUNZIP=1
unzip -qjo "$ZIPFILE" 'common/functions.sh' -d $TMPDIR >&2
. $TMPDIR/functions.sh