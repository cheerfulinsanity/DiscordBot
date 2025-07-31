def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info.
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        durationSeconds
        startDateTime
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
            campStack
            itemPurchases { itemId time }
            killEvents { time target }
            deathEvents { time }
            assistEvents { time target }
            wardDestruction {
              time
            }
          }
        }
      }
    }
    """
    variables = {"matchId": match_id}
    headers = HEADERS_TEMPLATE | {"Authorization": f"Bearer {token}"}

    try:
        res = requests.post(
            STRATZ_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=15
        )

        if res.status_code != 200:
            print(f"❌ Stratz returned HTTP {res.status_code}: {res.text}")
            return None

        data = res.json()

        if "errors" in data:
            print(f"❌ GraphQL errors from Stratz:\n{json.dumps(data['errors'], indent=2)}")
            return None

        if os.getenv("DEBUG_MODE") == "1":
            print("🔎 Full match response:")
            print(json.dumps(data, indent=2))

        return data.get("data", {}).get("match")

    except Exception as e:
        print(f"❌ Error in fetch_full_match: {e}")
        return None
