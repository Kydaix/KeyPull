build:
	@go build -o bin/keypull -ldflags "-s -w" cmd/keypull/main.go