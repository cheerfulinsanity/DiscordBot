import os
import requests

STRATZ_URL = "https://api.stratz.com/graphql"
TOKEN = os.getenv("TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "STRATZ_API",
    "Content-Type": "application/json",
}


def fetch_latest_match(steam_id):
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: {take: 1}) {
          id
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    response = requests.post(STRATZ_URL, headers=HEADERS, json={"query": query, "variables": variables})
    response.raise_for_status()
    data = response.json()
    try:
        return data["data"]["player"]["matches"][0]["id"]
    except (KeyError, IndexError):
        return None


def fetch_full_match(steam_id):
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: {take: 1}) {
          id
          durationSeconds
          startDateTime
          gameMode
          players {
            steamAccountId
            isVictory
            isRadiant
            lane
            role
            position
            partyId
            kills
            deaths
            assists
            goldPerMinute
            experiencePerMinute
            numLastHits
            imp
            item0Id
            item1Id
            item2Id
            item3Id
            item4Id
            item5Id
            neutral0Id
            backpack0Id
            backpack1Id
            backpack2Id
            isRandom
            intentionalFeeding
            hero {
              id
              name
            }
            stats {
              level
              itemPurchases {
                itemId
                time
              }
              killEvents {
                time
                target
              }
              deathEvents {
                time
              }
              assistEvents {
                time
                target
              }
            }
          }
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    response = requests.post(STRATZ_URL, headers=HEADERS, json={"query": query, "variables": variables})
    response.raise_for_status()
    return response.json()
