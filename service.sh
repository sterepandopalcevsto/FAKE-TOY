#!/system/bin/sh
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
  
  # GPU tweaks if available
  if [ -d "/sys/class/kgsl/kgsl-3d0" ]; then
    echo "1" > /sys/class/kgsl/kgsl-3d0/force_clk_on
    echo "1" > /sys/class/kgsl/kgsl-3d0/force_bus_on
    echo "0" > /sys/class/kgsl/kgsl-3d0/force_rail_on
    echo "GPU parameters tuned for battery saving" >> $LOG_FILE
  fi
  
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
  echo "Disabled unnecessary kernel wakelocks" >> $LOG_FILE
  
  # Disable thermal throttling (with caution)
  # for THERMAL in /sys/class/thermal/thermal_zone*/mode; do
  #   echo "disabled" > $THERMAL
  # done
  # echo "Disabled thermal throttling" >> $LOG_FILE
  
  # Network related tweaks
  echo "3" > /proc/sys/net/ipv4/tcp_fastopen
  echo "0" > /proc/sys/net/ipv4/tcp_timestamps
  echo "1" > /proc/sys/net/ipv4/tcp_sack
  echo "Optimized TCP parameters" >> $LOG_FILE
  
  # Aggressive doze mode
  if command -v settings > /dev/null; then
    settings put global device_idle_constants inactive_to=30000,light_after_inactive_to=10000
    echo "Tweaked doze parameters for faster entry to doze state" >> $LOG_FILE
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
        echo "Applied restrictions to $APP" >> $LOG_FILE
      fi
    done
    echo "Battery hungry apps have been optimized" >> $LOG_FILE
  else
    echo "appops command not found, skipping app-specific optimizations" >> $LOG_FILE
  fi
}

# Apply initial optimizations
apply_battery_optimizations
manage_battery_hungry_apps

# Periodic optimization (every 3 hours)
while true; do
  sleep 10800
  echo "Running periodic optimization at $(date)" >> $LOG_FILE
  apply_battery_optimizations
done