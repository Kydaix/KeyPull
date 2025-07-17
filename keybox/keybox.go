package keybox

import (
	"encoding/xml"
)

type Attestation struct {
	XMLName          xml.Name `xml:"AndroidAttestation"`
	NumberOfKeyboxes int      `xml:"NumberOfKeyboxes"`
	Keyboxes         []Keybox `xml:"Keybox"`
}

type Keybox struct {
	DeviceID string `xml:"DeviceID,attr"`
	Keys     []Key  `xml:"Key"`
}

type Key struct {
	Algorithm        string           `xml:"algorithm,attr"`
	PrivateKey       PrivateKey       `xml:"PrivateKey"`
	CertificateChain CertificateChain `xml:"CertificateChain"`
}

type PrivateKey struct {
	Format string `xml:"format,attr"`
	Data   string `xml:",chardata"`
}

type CertificateChain struct {
	NumberOfCertificates int           `xml:"NumberOfCertificates"`
	Certificates         []Certificate `xml:"Certificate"`
}

type Certificate struct {
	Format string `xml:"format,attr"`
	Data   string `xml:",chardata"`
}
