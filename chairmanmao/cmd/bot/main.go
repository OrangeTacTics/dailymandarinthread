package main

import (
    "time"
    "log"
    "os"
    "os/signal"
    "syscall"
    "fmt"
    "github.com/joho/godotenv"
    "github.com/bwmarrin/discordgo"
    "strings"
    "context"
    "github.com/segmentio/kafka-go"
    "github.com/go-redis/redis"
)

type UserId = string

type SyncBot struct {
    displayNames map[UserId]string

    session *discordgo.Session
    guildId string
    redis *redis.Client

    ctx context.Context

}

func New() *SyncBot {
    // Connect redis
    redis := redis.NewClient(
        &redis.Options{
            Addr: "localhost:6379",
        },
    )
    _, err := redis.Ping().Result()

    if err != nil {
        panic(err)
    }

    // Connect Discord
    discord := discordConnect()
    go onSignal(discord)

    discord.AddHandler(func(s *discordgo.Session, r *discordgo.Ready) {
        log.Println("ChairmanMao is online")
    })

    return &SyncBot {
        displayNames: make(map[UserId]string),
        session: discord,
        redis: redis,
        guildId: "929462140727861269",
        ctx: context.Background(),
    }
}

func (bot *SyncBot) reloadFromRedis() {
    keys, err := bot.redis.Keys("syncbot:display_name:*").Result()

    if err != nil {
        panic(err)
    }

    for _, key := range keys {
        fmt.Println(key)
        userId := strings.Split(key, ":")[2]
        displayName, err := bot.redis.Get(key).Result()

        if err != nil {
            panic(err)
        }

        bot.displayNames[userId] = displayName
    }
}

func findMemberByUserId(members []*discordgo.Member, userId UserId) *discordgo.Member {
    for _, member := range members {
        if member.User.ID == userId {
            return member
        }
    }
    return nil
}

func (bot *SyncBot) DirtyNickUsers() []UserId {
    members, err := bot.session.GuildMembers(bot.guildId, "", 1000)

    if err != nil {
        log.Fatal(err)
    }


    results := make([]UserId, 0)

    for userId, displayName := range bot.displayNames {
        member := findMemberByUserId(members, userId)

        if member != nil {
            currentDisplayName := member.Nick
            if currentDisplayName == "" {
                currentDisplayName = member.User.Username
            }

            if currentDisplayName != displayName {
                fmt.Printf("    dirty displayName: %s != %s\n", currentDisplayName, displayName)
                results = append(results, userId)
            }
        }
    }

    return results
}

func (bot *SyncBot) SyncUserNicks() {
    fmt.Println("Syncing")

    dirtyUserIds := bot.DirtyNickUsers()
    fmt.Printf("    %d dirty users found\n", len(dirtyUserIds))

    for _, userId := range dirtyUserIds {
        displayName := bot.displayNames[userId]
        fmt.Printf("    " + userId + " => " + displayName + " ")
        bot.session.GuildMemberNickname(bot.guildId, userId, displayName)
        fmt.Println("OK")
    }
}

func main() {
    bot := New()
    fmt.Println("Sync bot ready")

    members, err := bot.session.GuildMembers(bot.guildId, "", 1000)

    if err != nil {
        log.Fatal(err)
    }

    fmt.Println("Members:")
    for _, member := range members {
        fmt.Println("    " + member.User.ID + " " + member.User.Username)
    }

    for {
        bot.reloadFromRedis()
        bot.SyncUserNicks()
        time.Sleep(15 * time.Second)
    }

//    discord.AddHandler(messageCreate)
//
//
//
//    msgIn := make(chan string, 1)
//    go recvMessageLoop(msgIn)
//
//    for msg := range msgIn {
//        guildID := "929462140727861269"
//        userId := "878851905021947924"
//        newNick := msg
//        fmt.Println("Renaming to " + newNick)
//        discord.GuildMemberNickname(guildID, userId, newNick)
//    }
//
//    for {}
}

func discordConnect() *discordgo.Session {
    err := godotenv.Load()
    if err != nil {
        log.Fatal("Error loading .env file")
    }

    discordToken := os.Getenv("DISCORD_TOKEN")
    fmt.Println(discordToken)

    discord, err := discordgo.New("Bot " + discordToken)
    if err != nil {
        log.Fatal("error creating Discord session,", err)
    }
    discord.Identify.Intents = discordgo.IntentsAll

    err = discord.Open()
    if err != nil {
        log.Fatal("error opening connection,", err)
    }

    return discord
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

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {
    // Ignore all messages created by the bot itself
    // This isn't required in this specific example but it's a good practice.
    if m.Author.ID == s.State.User.ID {
        return
    }
    // In this example, we only care about messages that are "ping".
    if m.Content == "!ping" {
        // We create the private channel with the user who sent the message.
        channel, err := s.UserChannelCreate(m.Author.ID)
        if err != nil {
            // If an error occurred, we failed to create the channel.
            //
            // Some common causes are:
            // 1. We don't share a server with the user (not possible here).
            // 2. We opened enough DM channels quickly enough for Discord to
            //    label us as abusing the endpoint, blocking us from opening
            //    new ones.
            fmt.Println("error creating channel:", err)
            s.ChannelMessageSend(
                m.ChannelID,
                "Something went wrong while sending the DM!",
            )
            return
        }
        // Then we send the message through the channel we created.
        _, err = s.ChannelMessageSend(channel.ID, "Pong! " + m.Author.ID + " " + m.GuildID)
        if err != nil {
            // If an error occurred, we failed to send the message.
            //
            // It may occur either when we do not share a server with the
            // user (highly unlikely as we just received a message) or
            // the user disabled DM in their settings (more likely).
            fmt.Println("error sending DM message:", err)
            s.ChannelMessageSend(
                m.ChannelID,
                "Failed to send you a DM. "+
                    "Did you disable DM in your privacy settings?",
            )
        }
    } else if strings.HasPrefix(m.Content, "!displayName") {
        cmdParts := strings.Split(m.Content, " ")
        if len(cmdParts) > 1 {
            newNick := cmdParts[1]
            if len(newNick) <= 32 {
                s.GuildMemberNickname(m.GuildID, m.Author.ID, newNick)
                s.ChannelMessageSend(
                    m.ChannelID,
                    m.Author.Username + " is now known as " + newNick,
                )
            } else {
                // print help -- name too long
            }
        } else {
            // print help -- no name given
        }
    }
}

func recvMessageLoop(out chan string) {
    r := kafka.NewReader(
        kafka.ReaderConfig{
            Brokers:   []string{"localhost:39537"},
            Topic:     "foo",
            GroupID:   "bar",
            StartOffset: kafka.LastOffset,
        },
    )

    background := context.Background()

    for {
        m, err := r.ReadMessage(background)
        if err != nil {
            break
        }
        fmt.Println("Received message: " + string(m.Offset) + " " + string(m.Value))
        out<- string(m.Value)
    }

    if err := r.Close(); err != nil {
        log.Fatal("failed to close reader:", err)
    }
}
