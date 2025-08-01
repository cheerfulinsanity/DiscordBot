def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info (v4-ready).
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        gameMode
        durationSeconds
        startDateTime
        radiantNetworthLeads
        radiantExperienceLeads
        fightEvents {
          time
          team
          value
        }

        players {
          steamAccountId
          isVictory
          isRadiant
          lane
          role
          position
          partyId
          behavior
          intentionalFeeding

          # Combat + economy
          kills
          deaths
          assists
          imp
          gold
          goldSpent
          networth
          goldPerMinute
          experiencePerMinute
          level

          # Inventory
          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id
          backpack0Id
          backpack1Id
          backpack2Id
          neutral0Id

          # Hero identity
          hero {
            id
            name
            displayName
          }

          stats {
            level
            campStack
            healPerMinute
            heroDamagePerMinute
            towerDamagePerMinute
            networthPerMinute
            experiencePerMinute
            actionsPerMinute

            # Ward placement and destruction
            wards {
              time
              isObserver
              isSentry
            }
            wardDestruction {
              time
              isObserver
              isSentry
            }

            # Rune control
            runes {
              time
              type
            }

            # Courier kills
            courierKills {
              time
            }

            # Combat timeline events (optional)
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
    """
    variables = {"matchId": match_id}
    data = post_stratz_query(query, variables, token, timeout=15)

    if not data:
        return None

    if os.getenv("DEBUG_MODE") == "1":
        print("🔎 Full match response:")
        print(json.dumps(data, indent=2))

    return data.get("match")
