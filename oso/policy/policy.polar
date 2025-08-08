actor User {
  roles = ["Manager"];

  relations = { 
    company: Company,
    department: Department,
    team: Team
  };

  "Manager" if "Admin" on "company";
  "Manager" if "Head" on "department";
  "Manager" if "Manager" on "team";
}

resource Company {
  roles = ["Admin"];
}

resource Department {
  roles = ["Head"];
}

resource Team {
  roles = ["Manager"];
  relations = { parent_team: Team, managed_by: User };

  "Manager" if "Manager" on "parent_team";
  "Manager" if "managed_by";
}

resource Card {
    permissions = ["view"];
    relations = { owner: User };
    roles = ["Viewer"]; 

    "view" if "Viewer";

    "Viewer" if "owner";
    "Viewer" if "Manager" on "owner";
}

test fixture company_hierarchy {
  has_relation(User{"ash"}, "company", Company{"oso"});
  has_relation(User{"ash"}, "department", Department{"engineering"});
  has_relation(User{"ash"}, "team", Team{"customer-eng"});

  has_relation(User{"gabe"}, "company", Company{"oso"});
  has_relation(User{"gabe"}, "department", Department{"engineering"});
  has_relation(User{"gabe"}, "team", Team{"customer-eng"});
  has_role(User{"gabe"}, "Manager", Team{"customer-eng"});

  has_relation(User{"nick"}, "company", Company{"oso"});
  has_relation(User{"nick"}, "department", Department{"engineering"});
  has_role(User{"nick"}, "Head", Department{"engineering"});

  has_relation(User{"nick"}, "company", Company{"oso"});
  has_relation(User{"nick"}, "team", Team{"engineering"});
  has_relation(User{"nick"}, "department", Department{"engineering"});

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