#!/system/bin/sh
# Battery Optimizer Module
# Post-FS-Data script for Battery Optimizer

MODDIR=${0%/*}

# Create a log directory if it doesn't exist
mkdir -p $MODDIR/logs

# Apply early initialization battery tweaks
# These are applied before boot is completed

# Add kernel parameters to sysctl.conf if not already there
if [ -f /system/etc/sysctl.conf ]; then
  # Create a backup first
  cp /system/etc/sysctl.conf $MODDIR/sysctl.conf.bak
  
  # Add/modify battery saving parameters
  cat << EOF > $MODDIR/sysctl.conf
# Battery Optimizer Tweaks
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=80
vm.dirty_background_ratio=50
vm.dirty_expire_centisecs=3000
vm.dirty_writeback_centisecs=3000
kernel.random.read_wakeup_threshold=2048
kernel.random.write_wakeup_threshold=256
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_timestamps=0
net.ipv4.tcp_sack=1
EOF

  # Replace the original sysctl.conf with our modified one
  mount -o bind $MODDIR/sysctl.conf /system/etc/sysctl.conf
  
  # Apply the settings immediately
  sysctl -p /system/etc/sysctl.conf
fi

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

# Disable unnecessary services (with caution)
# This is just an example - be careful with disabling services
SERVICES_TO_DISABLE="
  print
  nfc
  bluetooth
"

if command -v pm > /dev/null; then
  for SERVICE in $SERVICES_TO_DISABLE; do
    pm disable $SERVICE >/dev/null 2>&1
  done
fi

exit 0