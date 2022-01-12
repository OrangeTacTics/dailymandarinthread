package main

import (
    "time"
    "os"
    "os/signal"
    "syscall"
    "fmt"
    "github.com/joho/godotenv"
    "github.com/bwmarrin/discordgo"
)

func main() {
    err := godotenv.Load()
    if err != nil {
        panic(err)
    }

    bot := New()
    go onSignal(bot.session)

    fmt.Println("Sync bot ready")

    members, err := bot.session.GuildMembers(bot.guildId, "", 1000)

    if err != nil {
        panic(err)
    }

    fmt.Println("Members:")
    for _, member := range members {
        fmt.Println("    " + member.User.ID + " " + member.User.Username)
    }

    for {
        bot.reloadFromRedis()
        bot.syncUsers()
        bot.syncEmojis()
        bot.syncEmojis()
        time.Sleep(15 * time.Second)
    }
}

func onSignal(discord *discordgo.Session) {
    fmt.Println("Press CTRL-C to exit.")
    sc := make(chan os.Signal, 1)
    signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt, os.Kill)
    signal := <-sc
    fmt.Println()
    fmt.Println("Received signal: ", signal)

    fmt.Println("Shutting down Discord...")
    discord.Close()
    fmt.Println("Good bye.")
    os.Exit(0)
}
