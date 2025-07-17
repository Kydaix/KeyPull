package extract

import (
	"log"
	"os"
	"path/filepath"
)

type Extractor struct {
	Device string
	Output string
}

func NewExtractor(output string) *Extractor {
	dir, err := os.Getwd()
	if err != nil {
		log.Fatal("Failed to get current directory:", err)
	}
	return &Extractor{
		Output: filepath.Join(dir, output),
	}
}
