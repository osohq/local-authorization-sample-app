actor User {
  relations = { manager: User };
}

resource Card {
  permissions = ["card.read"];

  relations = { owner: User };
  "card.read" if "owner";
}

has_permission(manager:User, permission:String, card:Card) if
  user matches User and
  has_relation(user, "manager", manager) and
  has_permission(user, permission, card);
