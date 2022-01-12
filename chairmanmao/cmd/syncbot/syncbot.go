package main

import (
//    "path/filepath"
    //"strings"
    "io/ioutil"
    "os"
    "fmt"
    "encoding/json"
    "github.com/go-redis/redis"
    "github.com/bwmarrin/discordgo"
)

func New() *SyncBot {
    guildId := os.Getenv("GUILD_ID")
    redisHost := os.Getenv("REDIS_HOST")

    // Connect redis
    redis := redis.NewClient(
        &redis.Options{
            Addr: redisHost,
        },
    )
    _, err := redis.Ping().Result()

    if err != nil {
        panic(err)
    }

    // Connect Discord
    discord := discordConnect()

    discord.AddHandler(func(s *discordgo.Session, r *discordgo.Ready) {
        fmt.Println("ChairmanMao is online")
    })

    return &SyncBot {
        users: make([]User, 0),
        roles: make([]Role, 0),
        emojis: make([]Emoji, 0),

        session: discord,
        redis: redis,
        guildId: guildId,
    }
}

func (bot *SyncBot) reloadUsersFromRedis() {
    users_json, err := bot.redis.Get("syncbot:users").Result()
    if err != nil {
        panic(err)
    }
    var users []User
    err = json.Unmarshal([]byte(users_json), &users)
    if err != nil {
        panic(err)
    }

    bot.users = make([]User, 0)
    for _, user := range users {
        bot.users = append(bot.users, user)
    }
}

func (bot *SyncBot) reloadRolesFromRedis() {
    roles_json, err := bot.redis.Get("syncbot:roles").Result()
    if err != nil {
        panic(err)
    }
    var roles []Role
    err = json.Unmarshal([]byte(roles_json), &roles)
    if err != nil {
        panic(err)
    }

    bot.roles = make([]Role, 0)
    for _, role := range roles {
        bot.roles = append(bot.roles, role)
    }
    fmt.Println("ROLES:", bot.roles)
}

func (bot *SyncBot) reloadEmojisFromRedis() {
    emojis_json, err := bot.redis.Get("syncbot:emojis").Result()
    if err != nil {
        panic(err)
    }
    var emojis []Emoji
    err = json.Unmarshal([]byte(emojis_json), &emojis)
    if err != nil {
        panic(err)
    }

    bot.emojis = make([]Emoji, 0)
    for _, emoji := range emojis {
        bot.emojis = append(bot.emojis, emoji)
    }
}

func (bot *SyncBot) reloadFromRedis() {
    bot.reloadUsersFromRedis()
    bot.reloadRolesFromRedis()
    bot.reloadEmojisFromRedis()
}

func discordConnect() *discordgo.Session {
    discordToken := os.Getenv("DISCORD_TOKEN")
    fmt.Println(discordToken)

    discord, err := discordgo.New("Bot " + discordToken)
    if err != nil {
        panic(err)
    }
    discord.Identify.Intents = discordgo.IntentsAll

    err = discord.Open()
    if err != nil {
        panic(err)
    }

    return discord
}

func (bot *SyncBot) uploadEmoji(emojiName EmojiName) *discordgo.Emoji {
    data, err := ioutil.ReadFile("emojis/" + emojiName + ".png")
    if err != nil {
        panic(err)
    }

    var roles []string = nil
    fmt.Println("Uploading emoji:", emojiName)
    emoji, err := bot.session.GuildEmojiCreate(bot.guildId, emojiName, bytesToUriString(data), roles)
    if err != nil {
        panic(err)
    }
    return emoji
}

func (bot *SyncBot) syncEmojis() {
    fmt.Println("Syncing Emojis")

    emojis, err := bot.session.GuildEmojis(bot.guildId)

    if err != nil {
        panic(err)
    }

    serverEmojiNames := make([]string, len(emojis))
    for i, emoji := range emojis {
        fmt.Println("   ", emoji.ID, emoji.Name)
        serverEmojiNames[i] = emoji.Name
    }


    desiredEmojiNames := make([]string, 0)
    for _, emoji := range bot.emojis {
        desiredEmojiNames = append(desiredEmojiNames, emoji.Name)
    }

    adds, mods, dels := addModDelOf(desiredEmojiNames, serverEmojiNames)
    fmt.Println(adds, mods, dels)

    for _, emojiName := range adds {
        bot.uploadEmoji(emojiName)
    }

    for _, emojiName := range dels {
        var emojiId string
        for _, emoji := range emojis {
            if emoji.Name == emojiName {
                emojiId = emoji.ID
                break
            }
        }
        err := bot.session.GuildEmojiDelete(bot.guildId, emojiId)
        if err != nil {
            panic(err)
        }
    }
}

func (bot *SyncBot) syncRoles() {
    roles, err := bot.session.GuildRoles(bot.guildId)
    if err != nil {
        panic(err)
    }
    currentRoleNames := make([]string, 0)
    for _, role := range roles {
        if role.Name != "@everyone" && role.Name != "ChairmanMao" {
            currentRoleNames = append(currentRoleNames, role.Name)
        }
    }

    desiredRoleNames  := make([]string, 0)
    for _, role := range bot.roles {
        desiredRoleNames = append(desiredRoleNames, role.Name)
    }

    fmt.Println("Desired:", desiredRoleNames)
    fmt.Println("Current:", currentRoleNames)

    adds, mods, dels := addModDelOf(desiredRoleNames, currentRoleNames)
    fmt.Println("Adds:", adds)
    fmt.Println("Mods:", mods)
    fmt.Println("Dels:", dels)

    for _, roleName := range adds {
        fmt.Println("Creating role", roleName)
        role, err := bot.session.GuildRoleCreate(bot.guildId)
        if err != nil {
            panic(err)
        }

        role.Name = roleName
        color := 0xff0000
        hoist := false
        var perm int64 = discordgo.PermissionSendMessages
        mention := true
        _, err = bot.session.GuildRoleEdit(bot.guildId, role.ID, roleName, color, hoist, perm, mention)

        if err != nil {
            panic(err)
        }
    }

    for _, roleName := range dels {
        fmt.Println("Deleting roleName", roleName)

        var roleId string
        for _, role := range roles {
            if role.Name == roleName {
                roleId = role.ID
                break
            }
        }
        err = bot.session.GuildRoleDelete(bot.guildId, roleId)

        if err != nil {
            panic(err)
        }
    }

    for _, roleName := range mods {
        fmt.Println("Modifying roleName", roleName)
        var roleId string
        for _, role := range roles {
            if role.Name == roleName {
                roleId = role.ID
                break
            }
        }
        color := 0xff0000
        hoist := false
        var perm int64 = discordgo.PermissionSendMessages
        mention := true
        _, err = bot.session.GuildRoleEdit(bot.guildId, roleId, roleName, color, hoist, perm, mention)

        if err != nil {
            panic(err)
        }
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
        panic(err)
    }


    results := make([]UserId, 0)

    for _, user := range bot.users {
        userId := user.Id
        displayName := user.DisplayName
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

func (bot *SyncBot) DirtyRoles() {
    roles, err := bot.session.GuildRoles(bot.guildId)
    if err != nil {
        panic(nil)
    }

    fmt.Println("DirtyRoles()")
    for _, role := range roles {
        fmt.Println("   ", role.ID, role.Name, role.Managed, role.Mentionable, role.Hoist, role.Color, role.Position, role.Permissions)
    }
}

func (bot *SyncBot) UserById(userId UserId) *User {
    for _, user := range bot.users {
        if user.Id == userId {
            return &user
        }
    }
    return nil
}

func (bot *SyncBot) RoleByName(roleName string) *Role {
    for _, role := range bot.roles {
        if role.Name == roleName {
            return &role
        }
    }
    return nil
}

func (bot *SyncBot) SyncUserNicks() {
    fmt.Println("Syncing")

    dirtyUserIds := bot.DirtyNickUsers()
    fmt.Printf("    %d dirty users found\n", len(dirtyUserIds))

    for _, userId := range dirtyUserIds {
        user := bot.UserById(userId)
        displayName := user.DisplayName
        fmt.Printf("    " + userId + " => " + displayName + " ")
        bot.session.GuildMemberNickname(bot.guildId, userId, displayName)
        fmt.Println("OK")
    }
}

func (bot *SyncBot) syncUsers() {
    memberById := make(map[UserId]*discordgo.Member)
    members, err := bot.session.GuildMembers(bot.guildId, "", 1000)
    if err != nil {
        panic(err)
    }

    for _, member := range members {
        memberById[member.User.ID] = member
    }

    roleById := make(map[RoleId]*discordgo.Role)
    roleByName := make(map[RoleName]*discordgo.Role)
    roles, err := bot.session.GuildRoles(bot.guildId)
    if err != nil {
        panic(err)
    }

    for _, role := range roles {
        roleById[role.ID] = role
        roleByName[role.Name] = role
    }

    fmt.Println("Syncing Users")

    for _, user := range bot.users {
        userId := user.Id
        displayName := user.DisplayName
        fmt.Println("    " + userId + " => " + displayName + " ")
        bot.session.GuildMemberNickname(bot.guildId, userId, displayName)

        member := memberById[userId]
        currentRoleNames := make([]RoleName, 0)
        for _, roleId := range member.Roles {
            role := roleById[roleId]
            currentRoleNames = append(currentRoleNames, role.Name)
        }
        fmt.Println("Comparing:", user.Roles, currentRoleNames)
        adds, mods, dels := addModDelOf(user.Roles, currentRoleNames)

        for _, add := range adds {
            role := roleByName[add]
            if role != nil {
                fmt.Println("Adding role", role.ID, role.Name)
                bot.session.GuildMemberRoleAdd(bot.guildId, userId, role.ID)
            } else {
                fmt.Println("Role does not exist, cannot add", role.ID, role.Name)
            }
        }

        fmt.Println("OK")
        fmt.Println("=>", adds, mods, dels)
    }
}
