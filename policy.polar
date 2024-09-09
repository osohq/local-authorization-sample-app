actor User {
  relations = { manager: User };
}

resource Card {
  permissions = ["card.read"];

  relations = { manager: User };
  "card.read" if "manager";
}
