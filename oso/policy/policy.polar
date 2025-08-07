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
  relations = { parent_team: Team, managed_by: User, department: Department };

  "Manager" if "managed_by";
  "Manager" if "Manager" on "parent_team";
  "Manager" if "Head" on "department";
}

resource Card {
    permissions = ["view"];
    relations = { owner: User };
    roles = ["Viewer"]; 

    "view" if "Viewer";

    "Viewer" if "owner";
    "Viewer" if "ExpenseManager" on "owner";
}
