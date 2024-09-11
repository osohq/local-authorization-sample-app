actor User {
  relations = { direct_manager: User };
  roles = ["manager"];

  "manager" if "direct_manager";
  "manager" if "manager" on "direct_manager";
}

resource Card {
    permissions = ["card.read"];
    relations = { owner: User };
    roles = ["reader"];

    "reader" if "owner";
    "reader" if "manager" on "owner";

    "card.read" if "reader";
}

test "hierarchy" {
    setup {
        has_relation(Card{"1"}, "owner", User{"alice"});
        has_relation(User{"alice"}, "direct_manager", User{"bhav"});
        has_relation(User{"bhav"}, "direct_manager", User{"crystal"});
        has_relation(User{"fergie"}, "direct_manager", User{"crystal"});
        has_relation(User{"crystal"}, "direct_manager", User{"dorian"});
    }

    assert allow(User{"alice"}, "card.read", Card{"1"});
    assert allow(User{"bhav"}, "card.read", Card{"1"});
    assert allow(User{"crystal"}, "card.read", Card{"1"});
    assert allow(User{"dorian"}, "card.read", Card{"1"});
    assert_not allow(User{"fergie"}, "card.read", Card{"1"});
}
