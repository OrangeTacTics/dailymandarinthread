package main

import (
    "flag"
    "log"
    "context"
    "fmt"
    "github.com/segmentio/kafka-go"
)

func main() {
    is_producer := flag.Bool("produce", false, "Produce instead of consume")
    flag.Parse()

    if *is_producer {
        produce()
    } else {
        consume()
    }
}

func consume() {
    r := kafka.NewReader(
        kafka.ReaderConfig{
            Brokers:   []string{"localhost:9092"},
            Topic:     "foo",
            Partition: 0,
            MinBytes:  10e3, // 10KB
            MaxBytes:  10e6, // 10MB
        },
    )

    for {
        m, err := r.ReadMessage(context.Background())
        if err != nil {
            break
        }
        fmt.Printf("message at offset %d: %s = %s\n", m.Offset, string(m.Key), string(m.Value))
    }

    if err := r.Close(); err != nil {
        log.Fatal("failed to close reader:", err)
    }
}

func produce() {
    // make a writer that produces to topic-A, using the least-bytes distribution
    fmt.Println("Conecting...")
    w := &kafka.Writer{
        Addr:     kafka.TCP("localhost:9092"),
        Topic:   "foo",
        Balancer: &kafka.LeastBytes{},
    }

    background := context.Background()
    fmt.Println("Writing three messages...")
    err := w.WriteMessages(
        background,
        kafka.Message{
            Key:   []byte("Key-A"),
            Value: []byte("Hello World!"),
        },
        kafka.Message{
            Key:   []byte("Key-B"),
            Value: []byte("One!"),
        },
        kafka.Message{
            Key:   []byte("Key-C"),
            Value: []byte("Two!"),
        },
    )
    fmt.Println("Done")
    if err != nil {
        log.Fatal("failed to write messages:", err)
    }

    if err := w.Close(); err != nil {
        log.Fatal("failed to close writer:", err)
    }
}
