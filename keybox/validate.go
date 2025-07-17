package keybox

import (
	"encoding/xml"
	"fmt"
	"os"
)

func Validate(path string) error {
	var attestation Attestation
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("Failed to open keybox file: %v", err)
	}
	if err := xml.Unmarshal(data, &attestation); err != nil {
		return fmt.Errorf("XML is invalid: %v", err)
	}
	fmt.Printf("Keyboxes found: %v\n", attestation.NumberOfKeyboxes)
	for i, keybox := range attestation.Keyboxes {
		fmt.Printf("Keybox %d - Device ID: %s\n", i+1, keybox.DeviceID)
		for j, key := range keybox.Keys {
			fmt.Printf("  Key %v: Algorithm=%v, Certificates=%v\n",
				j+1, key.Algorithm, key.CertificateChain.NumberOfCertificates)
		}
	}
	return nil
}
