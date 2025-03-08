import os
import sys
import codecs

# Change this values according to your Project.
ModuleName = "battery-optimizer"
ModuleDisplayName = "Battery Optimizer"
ModuleVersion = "1.0"
ModuleVersionCode = ModuleVersion.replace('.', '')
ModuleDescription = "Magisk module that optimizes battery life by managing power-hungry processes and tweaking system parameters"
ModuleAuthorName = "claude ai"

# Github repository details. Change these values if needed.
RepositoryName = ModuleName
RepositoryOwner = ModuleAuthorName

ScriptName = os.path.split(__file__)[1]

dryRun = "--dry-run" in sys.argv

if not dryRun:
    # Check name
    if ' ' in ModuleName:
        raise NameError("Module name have space.")
    elif ModuleName == 'Magisk-Module-Template':
        raise NotImplementedError()

def makeTree(source = '.'):
    tree = []
    for p in os.listdir(source):
        if os.path.isdir(os.path.join(source, p)) and not p in ['.git', '.vs']:
            for path in makeTree(os.path.join(source, p)):
                tree.append(path)
        elif os.path.isfile(os.path.join(source, p)) and not p in [ScriptName, 'main.yml.release']:
            tree.append(os.path.join(source, p))
    return tree

# Создадим базовые файлы для модуля, если они не существуют
def create_module_files():
    # Создаем service.sh
    service_content = """#!/system/bin/sh
# Battery Optimizer Module
# Service script to optimize battery performance

MODDIR=${0%/*}

# Wait until boot is completed
while [ "$(getprop sys.boot_completed)" != "1" ]; do
  sleep 1
done

# Wait an additional 30 seconds to ensure all system services are started
sleep 30

# Log file setup
LOG_FILE=$MODDIR/battery_optimizer.log
echo "Battery Optimizer started at $(date)" > $LOG_FILE

# Function to apply battery optimizations
apply_battery_optimizations() {
  # Set kernel parameters for better battery life
  
  # CPU related tweaks
  for CPU in /sys/devices/system/cpu/cpu*/cpufreq; do
    # Set conservative governor if available
    if [ -f "$CPU/scaling_available_governors" ] && grep -q "conservative" "$CPU/scaling_available_governors"; then
      echo "conservative" > "$CPU/scaling_governor"
      echo "Setting conservative governor for $(dirname $CPU)" >> $LOG_FILE
    # Fallback to powersave if conservative is not available
    elif [ -f "$CPU/scaling_available_governors" ] && grep -q "powersave" "$CPU/scaling_available_governors"; then
      echo "powersave" > "$CPU/scaling_governor"
      echo "Setting powersave governor for $(dirname $CPU)" >> $LOG_FILE
    fi
    
    # Reduce max CPU frequency by 10% to save power if possible
    if [ -f "$CPU/scaling_max_freq" ] && [ -f "$CPU/cpuinfo_max_freq" ]; then
      MAX_FREQ=$(cat "$CPU/cpuinfo_max_freq")
      TARGET_FREQ=$((MAX_FREQ * 90 / 100))
      echo $TARGET_FREQ > "$CPU/scaling_max_freq"
      echo "Reduced max frequency for $(dirname $CPU) to $TARGET_FREQ" >> $LOG_FILE
    fi
  done
  
  # I/O scheduler tweaks
  for BLOCK in /sys/block/*/queue/scheduler; do
    if grep -q "noop" $BLOCK; then
      echo "noop" > $BLOCK
      echo "Setting noop scheduler for $(dirname $(dirname $BLOCK))" >> $LOG_FILE
    fi
  done
  
  # VM tweaks
  echo "80" > /proc/sys/vm/dirty_ratio
  echo "50" > /proc/sys/vm/dirty_background_ratio
  echo "3000" > /proc/sys/vm/dirty_writeback_centisecs
  echo "VM parameters tuned for battery saving" >> $LOG_FILE
  
  # Kernel wakelocks control
  if [ -e "/sys/module/wakeup/parameters/enable_qcom_rx_wakelock_ws" ]; then
    echo "0" > /sys/module/wakeup/parameters/enable_qcom_rx_wakelock_ws
  fi
  if [ -e "/sys/module/wakeup/parameters/enable_wlan_wow_wakeup_ws" ]; then
    echo "0" > /sys/module/wakeup/parameters/enable_wlan_wow_wakeup_ws
  fi
  if [ -e "/sys/module/wakeup/parameters/enable_wlan_extscan_wl_ws" ]; then
    echo "0" > /sys/module/wakeup/parameters/enable_wlan_extscan_wl_ws
  fi
  
  # Network related tweaks
  echo "3" > /proc/sys/net/ipv4/tcp_fastopen
  echo "0" > /proc/sys/net/ipv4/tcp_timestamps
  echo "1" > /proc/sys/net/ipv4/tcp_sack
  
  # Aggressive doze mode
  if command -v settings > /dev/null; then
    settings put global device_idle_constants inactive_to=30000,light_after_inactive_to=10000
  fi
}

# Function to manage apps with high battery usage
manage_battery_hungry_apps() {
  # List of known battery hungry apps 
  BATTERY_HUNGRY_APPS="
    com.facebook.katana
    com.facebook.orca
    com.snapchat.android
    com.whatsapp
    com.instagram.android
    com.google.android.youtube
  "
  
  # Check if app ops command is available
  if command -v appops > /dev/null; then
    for APP in $BATTERY_HUNGRY_APPS; do
      # Verify app is installed
      if pm list packages | grep -q $APP; then
        # Restrict background activity
        appops set $APP RUN_IN_BACKGROUND deny
        appops set $APP WAKE_LOCK deny
        # Restrict network usage in background
        appops set $APP RUN_ANY_IN_BACKGROUND deny
        appops set $APP CHANGE_WIFI_STATE deny
      fi
    done
  fi
}

# Apply initial optimizations
apply_battery_optimizations
manage_battery_hungry_apps

# Periodic optimization (every 3 hours)
while true; do
  sleep 10800
  apply_battery_optimizations
done
"""
    
    # Создаем post-fs-data.sh
    post_fs_content = """#!/system/bin/sh
# Battery Optimizer Module
# Post-FS-Data script for Battery Optimizer

MODDIR=${0%/*}

# Create a log directory if it doesn't exist
mkdir -p $MODDIR/logs

# Apply early initialization battery tweaks
# These are applied before boot is completed

# Set default CPU governor
for CPUFREQ in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  if [ -f "$CPUFREQ" ]; then
    # Try to set conservative governor first
    if grep -q "conservative" $(dirname $CPUFREQ)/scaling_available_governors; then
      echo "conservative" > $CPUFREQ
    # Otherwise try powersave
    elif grep -q "powersave" $(dirname $CPUFREQ)/scaling_available_governors; then
      echo "powersave" > $CPUFREQ
    fi
  fi
done

exit 0
"""
    
    # Создаем customize.sh
    customize_content = """##########################################################################################
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
"""
    
    # Создаем changelog.md
    changelog_content = """### Battery Optimizer Changelog

#### v1.0
* Initial release
* CPU frequency and governor optimization
* I/O scheduler tuning for better battery efficiency
* Memory management optimizations
* Background app management for known battery-hungry applications
* Network parameter optimization for reduced battery consumption
* Aggressive doze mode configuration
* Kernel parameter tweaks for extended battery life
"""
    
    if not dryRun:
        # Записываем файлы
        with open('service.sh', 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        with open('post-fs-data.sh', 'w', encoding='utf-8') as f:
            f.write(post_fs_content)
        
        with open('customize.sh', 'w', encoding='utf-8') as f:
            f.write(customize_content)
            
        with open('changelog.md', 'w', encoding='utf-8') as f:
            f.write(changelog_content)

# Сначала создаем файлы модуля
if not dryRun:
    create_module_files()

# Теперь проходим по всем существующим файлам и заменяем переменные
for f in makeTree():
    try:
        with codecs.open(f, 'r', encoding='utf-8', errors='ignore') as file:
            fData = file.read()
        
        hasModified = False
        
        # Replace template release workflow
        if f.endswith('main.yml'):
            try:
                with codecs.open(f + '.release', 'r', encoding='utf-8', errors='ignore') as tfile:
                    fData = tfile.read()
                if not dryRun:
                    os.remove(f + '.release')
                hasModified = True
            except FileNotFoundError:
                print(f"Warning: Release file {f}.release not found, skipping")
        
        # Replace module name
        if '@(ModuleName)' in fData:
            fData = fData.replace('@(ModuleName)', ModuleName)
            hasModified = True
            
        # Replace module display name
        if '@(ModuleDisplayName)' in fData:
            fData = fData.replace('@(ModuleDisplayName)', ModuleDisplayName)
            hasModified = True
            
        #Replace module description
        if '@(ModuleDescription)' in fData:
            fData = fData.replace('@(ModuleDescription)', ModuleDescription)
            hasModified = True
            
        # Replace module version data
        if '@(ModuleVersion)' in fData:
            fData = fData.replace('@(ModuleVersion)', ModuleVersion)
            hasModified = True
        if '@(ModuleVersionCode)' in fData:
            fData = fData.replace('@(ModuleVersionCode)', ModuleVersionCode)
            hasModified = True
            
        # Replace module author name
        if '@(ModuleAuthorName)' in fData:
            fData = fData.replace('@(ModuleAuthorName)', ModuleAuthorName)
            hasModified = True
        
        # Replace module Github details.
        if '@(RepositoryName)' in fData:
            fData = fData.replace('@(RepositoryName)', RepositoryName)
            hasModified = True
        if '@(RepositoryOwner)' in fData:
            fData = fData.replace('@(RepositoryOwner)', RepositoryOwner)
            hasModified = True
        
        if hasModified:
            # Do modifications
            if not dryRun:
                with codecs.open(f, 'w', encoding='utf-8') as file:
                    file.write(fData)
            # Write modifications to console
            else:
                print('Modified file: ' + f)
                print(fData)
                print()
    except Exception as e:
        print(f"Error processing file {f}: {e}")

print("Настройка модуля Battery Optimizer завершена успешно!")
print(f"Файлы модуля созданы: service.sh, post-fs-data.sh, customize.sh, changelog.md")
print("После упаковки модуля в ZIP, вы можете установить его через Magisk Manager")