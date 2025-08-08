actor User {
  roles = ["ExpenseManager"];
  relations = { 
    company: Company,
    department: Department,
    team: Team
  };

  "ExpenseManager" if "Admin" on "company";
  "ExpenseManager" if "Head" on "department";
  "ExpenseManager" if "Manager" on "team";
}

resource Company {
  roles = ["Admin"];
}

resource Department {
  roles = ["Head"];
}

resource Team {
  roles = ["Manager"];
  relations = { parent_team: Team };

  "Manager" if "Manager" on "parent_team";
}

direct_manager(user: User, direct_manager: User) if
  team matches Team and
  has_relation(user, "team", team) and
  has_relation(direct_manager, "team", team) and
  has_role(direct_manager, "Manager", team) and
  user != direct_manager;

managed_by(user: User, manager: User) if
  team matches Team and
  has_relation(user, "team", team) and
  has_role(team, "Manager", manager) and 
  user != manager;

resource Card {
    permissions = ["view"];
    relations = { owner: User };
    roles = ["Viewer"]; 

    "view" if "Viewer";

    "Viewer" if "owner";
    "Viewer" if "ExpenseManager" on "owner";
}

test fixture company_hierarchy {
  has_relation(User{"ash"}, "company", Company{"oso"});
  has_relation(User{"ash"}, "team", Team{"customer-eng"});

  has_relation(User{"gabe"}, "company", Company{"oso"});
  has_relation(User{"gabe"}, "team", Team{"customer-eng"});

  has_relation(User{"nick"}, "company", Company{"oso"});
  has_relation(User{"nick"}, "team", Team{"engineering"});
  has_relation(Team{"engineering"}, "department", Department{"engineering"});

  has_relation(Team{"customer-eng"}, "managed_by", User{"gabe"});
  has_relation(Team{"customer-eng"}, "department", Department{"engineering"});

  has_role(User{"nick"}, "Head", Department{"engineering"});

  has_role(User{"graham"}, "Admin", Company{"oso"});
}

test "Who can view a card?" {
  setup {
    fixture company_hierarchy;
    has_relation(Card{"ash-card"}, "owner", User{"ash"});
    has_relation(Card{"gabe-card"}, "owner", User{"gabe"});
    has_relation(Card{"nick-card"}, "owner", User{"nick"});
    has_relation(Card{"graham-card"}, "owner", User{"graham"});
  }

  assert allow(user: User, "view", Card{"ash-card"}) iff user in [
    User{"ash"}, User{"gabe"}, User{"graham"}, User{"nick"}
  ];

  assert allow(user: User, "view", Card{"gabe-card"}) iff user in [
    User{"gabe"}, User{"graham"}, User{"nick"}
  ];

  assert allow(user: User, "view", Card{"nick-card"}) iff user in [
    User{"nick"}, User{"graham"}
  ];

  assert allow(user: User, "view", Card{"graham-card"}) iff user in [
    User{"graham"}
  ];
}