package extract

import (
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/EndowTheGreat/keypull/keybox"
)

func (ex *Extractor) ADBStat() error {
	if err := exec.Command("adb", "start-server").Run(); err != nil {
		return fmt.Errorf("failed to start ADB server: %v", err)
	}
	output, err := exec.Command("adb", "devices").Output()
	if err != nil {
		return fmt.Errorf("failed to fetch connected devices: %v", err)
	}
	devices := strings.Split(string(output), "\n")
	var connected []string
	for _, device := range devices {
		if strings.Contains(device, "device") && !strings.Contains(device, "List of devices") {
			d := strings.Fields(device)
			if len(d) >= 2 && d[1] == "device" {
				connected = append(connected, d[0])
			}
		}
	}
	if len(connected) == 0 {
		return fmt.Errorf("Could not find any connected devices via ADB")
	}
	ex.Device = connected[0]
	fmt.Printf("Connected to device: %s\n", ex.Device)
	return nil
}

func (ex *Extractor) pullKeybox(path string) error {
	if err := exec.Command("adb", "-s", ex.Device, "pull", path, filepath.Join(ex.Output, "keybox.xml")).Run(); err != nil {
		return fmt.Errorf("ADB Pull failed: %v", err)
	}
	fmt.Printf("Keybox extracted: %v\n", filepath.Join(ex.Output, "keybox.xml"))
	return keybox.Validate(filepath.Join(ex.Output, "keybox.xml"))
}

func (ex *Extractor) pullKeystore(path string) error {
	cmd := exec.Command("adb", "-s", ex.Device, "pull", path, filepath.Join(ex.Output, "persistent.sqlite"))
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ADB Pull failed: %v", err)
	}
	fmt.Printf("Keystore extracted: %v\n", filepath.Join(ex.Output, "persistent.sqlite"))
	return nil
}
