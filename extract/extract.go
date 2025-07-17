package extract

import (
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/EndowTheGreat/keypull/keybox"
)

func (ex *Extractor) ObtainRoot() error {
	err := exec.Command("adb", "-s", ex.Device, "root").Run()
	if err != nil {
		fmt.Printf("ADB root failed: %v\n", err)
		fmt.Println("Attempting via SU")
		if err := exec.Command("adb", "-s", ex.Device, "shell", "su", "-c", "id").Run(); err != nil {
			return fmt.Errorf("root access required but not available. Please root your device or enable root access in Developer Options")
		}
		fmt.Println("Obtained root Via SU")
		return nil
	}
	fmt.Println("Obtained root via ADB")
	time.Sleep(2 * time.Second)
	return nil
}

func (ex *Extractor) ExtractFromLocation(location string) error {
	switch {
	case strings.HasSuffix(location, ".xml"):
		return ex.pullKeybox(location)
	case strings.HasSuffix(location, ".sqlite"):
		return ex.pullKeystore(location)
	default:
		return ex.contents(location)
	}
}

func (ex *Extractor) contents(path string) error {
	output, err := exec.Command("adb", "-s", ex.Device, "shell", "find", path, "-type", "f").Output()
	if err != nil {
		return fmt.Errorf("failed to list directory contents: %v", err)
	}
	files := strings.Split(strings.TrimSpace(string(output)), "\n")
	for _, file := range files {
		if file == "" {
			continue
		}
		local := filepath.Join(ex.Output, strings.ReplaceAll(file, "/", "_"))
		if err := exec.Command("adb", "-s", ex.Device, "pull", file, local).Run(); err != nil {
			fmt.Printf("Failed to pull %s: %v\n", file, err)
			continue
		}
		if strings.Contains(file, "keybox") || strings.HasSuffix(file, ".xml") {
			if err := keybox.Validate(local); err == nil {
				fmt.Printf("Keybox located")
			}
		}
	}
	return nil
}
