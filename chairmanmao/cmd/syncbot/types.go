package main

import (
    "github.com/bwmarrin/discordgo"
    "github.com/go-redis/redis"
)

type UserId = string
type RoleId = string
type EmojiId = string
type EmojiName = string

type User struct {
    Id UserId `json:"user_id"`
    DisplayName string `json:"display_name"`
}

type Emoji struct {
    Name string `json:"name"`
}

type Role struct {
    Name string `json:"name"`
    Color int `json:"color"`
    Hoist bool `json:"hoist"`
    Mention bool `json:"mention"`
}

type SyncBot struct {
    users []User
    roles []Role
    emojis []Emoji

    session *discordgo.Session
    guildId string
    redis *redis.Client
}
