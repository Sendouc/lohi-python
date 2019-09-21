searchForBuildsByWeapon = """
query searchForBuildsByWeapon($weapon: String!, $page: Int) {
  searchForBuildsByWeapon(weapon: $weapon, page: $page) {
    builds {
      id
      discord_id
      title
      top
      headgear
      clothing
      shoes
      title
      updatedAt
      discord_user {
        username
        discriminator
      }
    }
    pageCount
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