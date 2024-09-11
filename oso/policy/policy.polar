actor User {
  relations = { direct_manager: User };
}

managed_by(employee: User, manager: User) if
  has_relation(employee, "direct_manager", manager);

managed_by(employee: User, manager: User) if
  middle_manager matches User and
  has_relation(employee, "direct_manager", middle_manager) and
  managed_by(middle_manager, manager);

has_role(user: User, "viewer", card: Card) if
    card_owner matches User and
    has_relation(card, "owner", card_owner) and
    managed_by(card_owner, user);

resource Card {
    permissions = ["view"];
    relations = { owner: User };
    roles = ["viewer"];

    "viewer" if "owner";

    "view" if "viewer";
}

test "hierarchy" {
    setup {
        has_relation(Card{"1"}, "owner", User{"alice"});
        has_relation(User{"alice"}, "direct_manager", User{"bhav"});
        has_relation(User{"bhav"}, "direct_manager", User{"crystal"});
        has_relation(User{"fergie"}, "direct_manager", User{"crystal"});
        has_relation(User{"crystal"}, "direct_manager", User{"dorian"});
    }

    assert allow(User{"alice"}, "view", Card{"1"});
    assert allow(User{"bhav"}, "view", Card{"1"});
    assert allow(User{"crystal"}, "view", Card{"1"});
    assert allow(User{"dorian"}, "view", Card{"1"});
    assert_not allow(User{"fergie"}, "view", Card{"1"});
}
