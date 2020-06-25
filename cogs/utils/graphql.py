searchForBuildsByWeapon = """
query searchForBuilds($discord_id: String, $weapon: String) {
    searchForBuilds(discord_id: $discord_id, weapon: $weapon) {
      id
      weapon
      title
      description
      headgear
      headgearItem
      clothing
      clothingItem
      shoes
      shoesItem
      updatedAt
      top
      discord_user {
        username
        discriminator
        discord_id
      }
    }
  }
"""

searchForBuilds = """
query searchForBuilds($discord_id: String!) {
  searchForBuilds(discord_id: $discord_id) {
    id
    weapon
    title
    headgear
    clothing
    shoes
    updatedAt
    top
  }
}
"""

maplists = """
{
  maplists {
    name
    sz
    tc
    rm
    cb
  }
}
"""

hasAccess = """
query hasAccess($discord_id: String!) {
  hasAccess(discord_id: $discord_id) 
}
"""

xPowers = """
query xPowers($discord_id: String!) {
  xPowers(discord_id: $discord_id) 
}
"""

addCompetitiveFeedEvent = """
mutation addCompetitiveFeedEvent(
    $event: CompetitiveFeedEventInput!
    $lohiToken: String!
  ) {
    addCompetitiveFeedEvent(
      event: $event
      lohiToken: $lohiToken
    )
  }
"""

usersForAvas = """
{
  users {
    discord_id
    avatar
  }
}
"""

updateAvas = """
mutation updateAvatars($lohiToken: String!, $toUpdate: [DiscordIdAvatar!]!) {
    updateAvatars(lohiToken: $lohiToken, toUpdate: $toUpdate)
  }
"""
