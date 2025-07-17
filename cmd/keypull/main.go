package main

import (
	"fmt"
	"log"
	"os"

	"github.com/EndowTheGreat/keypull/extract"
)

var extracted []string

func main() {
	fmt.Println("Instantiating extraction process...")
	extractor := extract.NewExtractor("output")
	if err := extractor.ADBStat(); err != nil {
		log.Fatalf("ADB connection failed: %v", err)
	}
	if err := extractor.ObtainRoot(); err != nil {
		log.Fatalf("Failed to obtain root: %v", err)
	}
	if err := os.MkdirAll(extractor.Output, 0o755); err != nil {
		log.Fatalf("Could not create output directory: %v", err)
	}
	for _, location := range extract.DeviceLocations {
		fmt.Printf("Attempting extraction: %s\n", location)
		if err := extractor.ExtractFromLocation(location); err != nil {
			fmt.Printf("  Failed: %v\n", err)
			continue
		}
		extracted = append(extracted, location)
		fmt.Printf("  Success: %s\n", location)
	}
	if len(extracted) == 0 {
		fmt.Println("Keybox extraction failed.")
		return
	}
	fmt.Printf("Extracted keybox data from %d location(s):\n", len(extracted))
	for _, location := range extracted {
		fmt.Printf("  - %s\n", location)
	}
	fmt.Printf("\nExtraction saved to: %s\n", extractor.Output)
}
