// ITS 241 — Database Management Systems (Coronel 14e + Havelka lectures)

const SD_DATA_MGMT_SRC = [
  { title: 'ITS 241: Introduction to Data Management — Data Management in Organization lectures (Havelka)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.1)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Chs 1–3)' },
];

const SD_DATA_MODELING_SRC = [
  { title: 'ITS 241: Data Modeling Fundamentals & Data Abstraction lectures (Havelka)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.2)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 2)' },
];

const SD_RELATIONAL_DB_SRC = [
  { title: 'ITS 241: The Relational Database Model lecture slides (Coronel Module 3)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.3)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 3)' },
];

const SD_ERD_SRC = [
  { title: 'ITS 241: Entity Relationship Diagrams lecture slides (Coronel Module 4)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.4)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 4–5)' },
];

const SD_NORMALIZATION_SRC = [
  { title: 'ITS 241: Normalization of Database Tables lecture slides (Coronel Module 6)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.5)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 6)' },
];

const SD_BI_DW_SRC = [
  { title: 'ITS 241: Business Intelligence and Data Warehouses lecture slides (Coronel Module 13)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.6)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 13)' },
];

const SD_SQL_FUND_SRC = [
  { title: 'ITS 241: Introduction to SQL — SELECT, WHERE, ORDER BY lecture slides (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
];

const SD_SQL_JOINS_SRC = [
  { title: 'ITS 241: SQL JOINs & Aggregate Functions lecture slides (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
];

const SD_SQL_ADV_SRC = [
  { title: 'ITS 241: SQL Subqueries, Functions & Set Operators lecture slides (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
  { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
];

export const GLOSSARY_databases = [

  // ── sd-data-mgmt-intro ────────────────────────────────────────────────────

  {
    m: ['database vs file system', 'file system limitations', 'evolution of data management'],
    d: 'A «database» is a shared, integrated structure storing a collection of data managed through a DBMS, solving the problems of flat file systems: «data redundancy», ad-hoc query cost, structural inflexibility, and inadequate security.',
    how: 'A file system tightly couples each application program to a private data file (structural dependence). A DBMS decouples applications from storage: you query the DBMS, which handles physical layout, access paths, and multi-user control. Databases evolved from single-file (1970s) → master/transaction files (1980s) → full DBMS.',
    ex: 'A 1980s payroll app owned its own EMPLOYEE.dat file. If HR updated an employee\'s address in their separate system, the two files would diverge—an update anomaly. A shared DBMS with a single EMPLOYEE table eliminates this.',
    mk: 'Confusing "database" with "DBMS": the database is the data itself; the DBMS is the software (Oracle, MySQL, MongoDB) that manages it.',
    src: SD_DATA_MGMT_SRC,
  },
  {
    m: ['DBMS functions', 'DBMS advantages', 'database management system'],
    d: 'A DBMS (database management system) is software that provides «data dictionary management», data storage management, security, multi-user access control, backup/recovery, data integrity, and application interfaces—making data independently accessible from any application.',
    how: 'DBMS advantages over file systems: improved data sharing & access control; better data security; minimized data inconsistency (each item stored once); improved ad-hoc query capability; increased end-user productivity. Costs include hardware/software investment, complexity, and vendor dependence.',
    ex: 'Oracle and MySQL both handle concurrent transactions from thousands of users, enforce constraints, and log changes for recovery—all transparently to the application code.',
    mk: 'Listing only advantages: always weigh DBMS costs (complexity, maintenance, vendor lock-in, upgrade risk) against the benefits.',
    src: SD_DATA_MGMT_SRC,
  },
  {
    m: ['data redundancy', 'data anomalies', 'data integrity', 'update anomaly', 'insertion anomaly', 'deletion anomaly'],
    d: '«Data redundancy» is the unnecessary storage of the same data in multiple places, causing «data inconsistency» and three types of anomalies: «update anomalies» (one copy changed, others not), «insertion anomalies» (can\'t add a row without unrelated data), and «deletion anomalies» (deleting one fact accidentally removes another).',
    how: 'File systems promote redundancy because each department creates its own files. The DBMS controls redundancy through normalization and foreign keys—each data item ideally stored once. Controlled redundancy is sometimes intentional (historical accuracy, performance).',
    ex: 'In a flat ORDERS file storing customer address with every order row, changing a customer\'s address requires updating dozens of rows; missing one creates an inconsistency.',
    mk: 'Thinking all redundancy is bad: sometimes denormalization (controlled redundancy) is used deliberately to speed up analytical queries.',
    src: SD_DATA_MGMT_SRC,
  },
  {
    m: ['data independence', 'structural independence', 'logical independence', 'physical independence'],
    d: '«Data independence» is the ability to change data storage characteristics without impacting applications. «Structural independence» means applications are unaffected by changes to the file structure; «logical independence» means the conceptual schema can change without breaking application code; «physical independence» means physical storage can change without affecting the DBMS schema.',
    how: 'Without a DBMS every program must specify the file name, record length, field definitions, and processing logic—tight structural and data dependence. The DBMS inserts a separation layer: the logical format (how apps see data) is decoupled from the physical format (how bits are stored on disk).',
    ex: 'Adding a new column to a CUSTOMER table in a DBMS doesn\'t break existing application queries that don\'t reference that column—logical independence. Moving the table to a different disk array doesn\'t change the SQL—physical independence.',
    mk: 'Treating logical and physical independence as the same: logical independence concerns the DBMS-level schema; physical concerns the storage architecture (disks, indexes, partitions).',
    src: SD_DATA_MGMT_SRC,
  },
  {
    m: ['database system components', 'five components of database system', 'hardware software people procedures data'],
    d: 'A database system consists of five components: «hardware» (servers, disks, network, user devices), «software» (OS, DBMS, utilities, apps), «people» (DBAs, designers, developers, end users), «procedures» (rules and instructions), and «data» (actual values for data elements). The DBMS is the intermediary between users/apps and the stored data.',
    how: 'The data can only be accessed through the DBMS—not directly by file I/O. This means security, integrity, and concurrency are centralized. DBAs manage the overall system; designers create the schema; developers write apps; end users query or update data.',
    ex: 'A hospital information system: servers (hardware), Oracle DBMS + EMR app (software), nurses/doctors/DBAs (people), HIPAA access protocols (procedures), patient records (data).',
    mk: 'Forgetting that "data" and "database" are separate components—the database stores structured data, while the data itself is the values filling that structure.',
    src: SD_DATA_MGMT_SRC,
  },

  // ── sd-data-modeling ──────────────────────────────────────────────────────

  {
    m: ['data model purpose', 'data modeling', 'data model components'],
    d: 'A «data model» is a graphical and narrative representation of real-world data structures, showing entities, attributes, associations, and constraints within a specific domain. Its purpose is to foster «shared understanding» between users and developers, represent requirements, and drive correct database design.',
    how: 'The modeling process is iterative: begin with an external (user) view, refine into a comprehensive conceptual schema, then derive the physical implementation. Components are: Entity (the "things"), Attribute (properties of things), Association (how things relate), and Constraint (rules restricting valid data).',
    ex: 'An e-commerce data model has entities CUSTOMER, ORDER, PRODUCT; attributes like CustomerID and ProductPrice; associations like "CUSTOMER places ORDER"; and constraints like "each ORDER must have at least one PRODUCT."',
    mk: 'Stopping at a vague diagram: the "final" model must include both a graphical depiction and a narrative describing rules and constraints, because diagrams alone can\'t capture all integrity requirements.',
    src: SD_DATA_MODELING_SRC,
  },
  {
    m: ['entity', 'attribute', 'association', 'constraint', 'data model building blocks'],
    d: 'An «entity» is a set of similar things we want to manage (corresponds to a table); an «attribute» is a specific piece of data tracked about an entity (a column); an «association» defines how entities relate to each other; a «constraint» is a rule that must be enforced to ensure data quality.',
    how: 'To implement a model you need: a structural description (entities & attributes), rules for integrity (constraints, relationships), and a way to manipulate data (CRUD operations). Attributes are defined by data type, value range, and size.',
    ex: 'STUDENT entity; attributes: StudentID (PK), Name, DOB, GPA; association: "STUDENT enrolls in COURSE" (M:N); constraint: GPA must be between 0.0 and 4.0.',
    mk: 'Confusing entities with instances: an entity represents the entire SET (like the CUSTOMER table), not a single customer row, which is an entity instance or occurrence.',
    src: SD_DATA_MODELING_SRC,
  },
  {
    m: ['three-schema architecture', 'external schema', 'conceptual schema', 'internal schema', 'ANSI/SPARC'],
    d: 'The three-schema architecture separates data views into: «external schema» (end-user/application subschemas, specific subsets), «conceptual schema» (the comprehensive global logical design, SW and HW independent), and «internal schema» (DBMS-dependent implementation using DDL: tables, indexes, access paths).',
    how: 'The external level contains multiple user views (subschemas). The conceptual level integrates all external views into a single consistent design—this is the ER diagram. The internal level is where you write DDL (CREATE TABLE, CREATE INDEX) in a specific RDBMS. The physical level (below the schema) is how the DBMS actually stores bits to disk.',
    ex: 'A university DB: the registrar\'s view shows ENROLLMENT data; the payroll view shows SALARY data—both are external schemas drawn from the same conceptual schema. Oracle translates that into B-tree indexes and tablespace allocations at the internal/physical level.',
    mk: 'Conflating conceptual and internal: the conceptual schema is DBMS-independent (ER model); the internal schema is software-dependent (Oracle DDL vs. MySQL DDL).',
    src: SD_DATA_MODELING_SRC,
  },
  {
    m: ['logical data model', 'physical data model', 'logical vs physical'],
    d: 'A «logical data model» is software and hardware independent, representing the business meaning of data (entities, relationships, attributes); a «physical data model» is DBMS- and hardware-dependent, specifying actual storage structures, data types, indexes, and partitioning strategies.',
    how: 'We use ER diagrams for logical modeling. The internal (logical in DBMS terms) model translates the ER to relational tables using DDL—software dependent but hardware independent. The physical model adds index types, tablespace assignments, and I/O tuning—both software and hardware dependent.',
    ex: 'Logical: CUSTOMER has CustomerID (PK), Name, Email. Physical: CUSTOMER table in Oracle with CustomerID as NUMBER(10) with a B-tree index, stored in the USERS tablespace on a 1TB SSD.',
    mk: 'Calling the relational table design "physical": tables defined with DDL are the internal/logical-DBMS level. True physical design includes storage allocation, buffer pools, and partition strategies.',
    src: SD_DATA_MODELING_SRC,
  },
  {
    m: ['data abstraction', 'logical independence DBMS', 'physical independence DBMS'],
    d: '«Data abstraction» uses the three-schema separation to enable change at one level without affecting others. «Logical (data) independence» means changing the internal schema (switching DBMS) does not require changing the conceptual design. «Physical independence» means changing hardware or storage architecture does not require changing the DBMS internal schema.',
    how: 'If we change the logical model (conceptual schema) we must update internal and physical. If we change the internal model (e.g., migrate from Oracle to PostgreSQL), we rewrite DDL but the ER design is unchanged. If we change the physical (new disk architecture), the DBMS adapts without altering schema definitions.',
    ex: 'A company migrates from Oracle to PostgreSQL: they rewrite CREATE TABLE DDL (internal change) but the ER diagram and application queries remain the same—logical independence at work.',
    mk: 'Thinking independence is absolute: logical independence is a goal, but complex stored procedures and proprietary SQL extensions can create hidden dependencies between the conceptual and internal levels.',
    src: SD_DATA_MODELING_SRC,
  },

  // ── sd-relational-db ──────────────────────────────────────────────────────

  {
    m: ['relational table characteristics', 'relation', 'tuple', 'domain relational'],
    d: 'A relational table (relation) is a two-dimensional structure of rows (tuples) and columns (attributes) where: each row represents one entity occurrence; each column has a distinct name and a specific «domain» (set of allowable values); each row-column intersection holds exactly one atomic value; row and column order are immaterial to the DBMS.',
    how: 'Eight key characteristics (Coronel Table 3.1): table perceived as 2D; each row is one entity instance; each column is an attribute; each cell is a single value; all values in a column share a format; each column has an attribute domain; row/column order is immaterial; each table must have a unique-row identifier (PK).',
    ex: 'PRODUCT table: columns P_CODE, P_DESCRIPT, P_PRICE, V_CODE. Each row is one product. P_PRICE domain is positive numbers ≤ 9999.99. Row order can change without affecting queries.',
    mk: 'Storing multiple values in a single cell (repeating groups): this violates 1NF and breaks the relational model.',
    src: SD_RELATIONAL_DB_SRC,
  },
  {
    m: ['keys relational model', 'primary key', 'foreign key', 'candidate key', 'composite key', 'superkey'],
    d: 'A «primary key (PK)» uniquely identifies each row and cannot be null. A «foreign key (FK)» is an attribute in one table that references the PK of another table, enforcing referential integrity. A «candidate key» is a minimal superkey. A «composite key» spans multiple attributes. A «superkey» is any key that uniquely identifies rows.',
    how: 'Key hierarchy: superkey → candidate key → primary key. Entity integrity: no PK attribute can be null. Referential integrity: every FK value must either match an existing PK or be null. A null in an FK means the relationship is optional/unknown.',
    ex: 'STUDENT(StudentID PK, Name, MajorID FK→MAJOR.MajorID). StudentID is the PK; MajorID is a FK. If a student has no declared major, MajorID is null—allowed. A MajorID value of 99 that has no matching row in MAJOR violates referential integrity.',
    mk: 'Confusing null with zero or empty string: null means "unknown or not applicable," while 0 and "" are actual values with meaning.',
    src: SD_RELATIONAL_DB_SRC,
  },
  {
    m: ['functional dependency', 'determination', 'full functional dependency', 'determinant'],
    d: '«Functional dependency» (FD) means the value of one or more attributes (the «determinant») determines the value of one or more other attributes. Written A → B: knowing A tells you exactly what B is. «Full functional dependency» means the entire determinant is necessary—no subset of it also determines B.',
    how: 'FDs are the foundation of normalization. To identify them: for each pair of attributes, ask "if I know A, do I always know B?" If yes, A → B. The determinant is also called the key; the determined attribute is the dependent. Partial dependency (used in 2NF) occurs when only part of a composite key determines a non-key attribute.',
    ex: 'In an INVOICE table: InvoiceID → CustomerName (knowing the invoice ID determines the customer). But in INVOICE_ITEM(InvoiceID, ProductID, ProductName): ProductID → ProductName is a partial dependency on the composite PK (InvoiceID, ProductID).',
    mk: 'Reversing causality: A → B does not mean B → A. InvoiceID → CustomerName does not mean CustomerName → InvoiceID (multiple invoices can have the same customer).',
    src: SD_RELATIONAL_DB_SRC,
  },
  {
    m: ['data dictionary', 'system catalog', "designer's database"],
    d: 'The «data dictionary» (system catalog) is a DBMS-managed metadata store that describes the database structure itself: table names, column names, data types, domains, PKs, FKs, indexes, views, and users. It is sometimes called "the database designer\'s database" because it stores what the designer cares about.',
    how: 'The data dictionary is just another set of tables managed by the DBMS—it stores metadata as ordinary relational data. DBAs and tools query it the same way applications query user data. It enables the DBMS to enforce constraints (FKs, NOT NULL, CHECK) automatically.',
    ex: 'In Oracle, SELECT * FROM ALL_TABLES returns a row for every table the current user can see—that query hits the data dictionary. The dictionary entry for CUSTOMER records that CustomerID is NUMBER(10) NOT NULL PRIMARY KEY.',
    mk: 'Confusing the data dictionary with the database itself: the dictionary stores *descriptions* of data structures, not the actual user data rows.',
    src: SD_RELATIONAL_DB_SRC,
  },
  {
    m: ['index database', 'unique index', 'index key'],
    d: 'A database «index» is an ordered structure that provides a fast lookup path to rows in a table, using an «index key» (one or more columns) as the reference point. A «unique index» ensures index-key values are distinct. Tables can have many indexes, each associated with one table.',
    how: 'Indexes improve read performance (SELECT, JOIN) at the cost of write performance (INSERT, UPDATE, DELETE must maintain every index). Primary keys are automatically indexed. DBAs create additional indexes on frequently filtered or joined columns. The trade-off: many indexes slow writes and consume disk space.',
    ex: 'CUSTOMER table with an index on LastName: a query WHERE LastName = \'Smith\' scans the B-tree index in O(log n) rather than scanning all rows. Without the index, the DBMS must do a full table scan.',
    mk: 'Indexing every column: over-indexing slows INSERT/UPDATE/DELETE and wastes space. Index selectively—high-cardinality columns used in WHERE clauses and JOIN conditions.',
    src: SD_RELATIONAL_DB_SRC,
  },

  // ── sd-erd ────────────────────────────────────────────────────────────────

  {
    m: ['ERD components', 'entity relationship diagram', 'ERM', 'entity relationship model'],
    d: 'An ERD (Entity-Relationship Diagram) is a graphical representation of the conceptual database schema, showing «entities» (rectangles, representing tables), «attributes» (ovals or listed columns), and «relationships» (lines connecting entities named with active/passive verbs). ERDs depict the end-user\'s view of the data.',
    how: 'Three common notations: Chen (circles for attributes), Crow\'s Foot (crows-foot symbols for cardinality), and UML. Entity names are nouns in ALL CAPS. Relationship names are verbs: "STUDENT enrolls in COURSE." Relationships operate in both directions: a student enrolls in courses; a course is enrolled in by students.',
    ex: 'CUSTOMER ──places──► ORDER ──contains──► PRODUCT. Each entity rectangle, each relationship line. The crow\'s foot at ORDER indicates many orders per customer.',
    mk: 'Confusing entity (the set/table) with entity instance (a single row): CUSTOMER is the entity; "Jane Smith, CustomerID 42" is an entity instance.',
    src: SD_ERD_SRC,
  },
  {
    m: ['cardinality', 'connectivity', '1:1', '1:M', 'M:N', 'one-to-many', 'many-to-many'],
    d: '«Connectivity» classifies relationships as 1:1, 1:M, or M:N. «Cardinality» expresses the minimum and maximum entity occurrences in a relationship, noted as (min, max) beside each entity end. A minimum of 0 means optional participation; a minimum of 1 means mandatory.',
    how: 'To determine connectivity: "Can one A be associated with many Bs? Can one B be associated with many As?" If A→many B, B→one A: 1:M. If both directions are many: M:N. M:N relationships must be resolved into two 1:M relationships through a bridge (associative/junction) table containing the PKs of both entities.',
    ex: 'CUSTOMER (1) ── places ──► (M) ORDER: one customer places many orders, each order belongs to one customer (1:M). STUDENT (M) ── enrolls ──► (N) CLASS: resolved via ENROLLMENT(StudentID FK, ClassID FK).',
    mk: 'Leaving M:N relationships unresolved in a physical design: relational databases cannot directly implement M:N—you must create a junction table.',
    src: SD_ERD_SRC,
  },
  {
    m: ['weak entity', 'strong entity', 'existence dependent', 'existence independent'],
    d: 'A «weak entity» is existence-dependent (cannot exist without a related parent entity) and its PK contains a FK component from the parent. A «strong entity» (regular entity) is existence-independent: it can exist without any other entity.',
    how: 'Weak entity test: (1) Is it existence-dependent? (2) Does its PK contain a FK from the parent? Both must be true. Example: DEPENDENT(EmpID FK, DepName) is a weak entity—it can\'t exist without an EMPLOYEE and its PK includes EmpID. EMPLOYEE is a strong entity.',
    ex: 'COURSE (strong) generates CLASS (weak). A CLASS section cannot exist without a parent COURSE; the CLASS PK includes CourseID from COURSE.',
    mk: 'Confusing optional participation with weakness: an entity with an optional FK relationship is not necessarily weak. A weak entity specifically requires both existence-dependence AND a PK that includes a FK component.',
    src: SD_ERD_SRC,
  },
  {
    m: ['relationship strength', 'identifying relationship', 'non-identifying relationship', 'weak relationship', 'strong relationship'],
    d: 'A «strong (identifying) relationship» exists when the PK of the related (child) entity contains a PK component from the parent entity—the child\'s identity depends on the parent. A «weak (non-identifying) relationship» exists when the child entity\'s PK does not contain a component from the parent\'s PK.',
    how: 'In Crow\'s Foot notation, strong relationships are shown with a solid line; weak relationships use a dashed line. Relationship strength is independent of cardinality: a 1:M relationship can be either strong or weak depending on whether the child\'s PK includes the parent\'s PK.',
    ex: 'Strong: COURSE(CourseID PK) → CLASS(CourseID FK + SectionNo → composite PK). Weak: CUSTOMER(CustomerID PK) → ORDER(OrderID PK, CustomerID FK)—OrderID alone uniquely identifies orders without CustomerID.',
    mk: 'Equating weak relationship with weak entity: a weak relationship does not automatically create a weak entity. A weak entity is a specific design pattern; weak relationships are simply FK references that are not part of the child\'s PK.',
    src: SD_ERD_SRC,
  },
  {
    m: ['composite attribute', 'derived attribute', 'multivalued attribute', 'simple attribute', 'optional attribute', 'required attribute'],
    d: 'Attribute types: «simple» (cannot be subdivided), «composite» (can be split—e.g., FullName → FirstName + LastName), «derived» (calculated from other attributes—e.g., Age from DOB), «multivalued» (can have multiple values—e.g., Phone), «required» (must have a value), «optional» (can be null).',
    how: 'Handling multivalued attributes: either create multiple columns (PhoneHome, PhoneCell) or create a separate entity (PHONE(CustomerID FK, PhoneType, PhoneNumber)). Derived attributes are often not stored in the DB—computed at query time—though sometimes stored for performance.',
    ex: 'STUDENT entity: StudentID (simple, required, PK), FullName (composite → FirstName, LastName), GPA (derived from grades), PhoneNumbers (multivalued → resolved to STUDENT_PHONE table), Nickname (simple, optional).',
    mk: 'Storing derived attributes unnecessarily: derived values that change frequently (age, running totals) create update anomalies when re-computed but not synchronized.',
    src: SD_ERD_SRC,
  },

  // ── sd-normalization ──────────────────────────────────────────────────────

  {
    m: ['normalization', 'normalization purpose', 'normal forms overview', 'denormalization'],
    d: '«Normalization» is the process of evaluating and correcting table structures to minimize data redundancy and eliminate data anomalies by assigning attributes to tables based on functional dependencies. It progresses through «normal forms» (1NF → 2NF → 3NF → BCNF). «Denormalization» intentionally reverses normalization for performance, accepting controlled redundancy.',
    how: 'The normalization goal: each table represents a single subject; each row-column intersection is one atomic value; no unnecessary redundancy; all non-key attributes depend on the full PK; no insertion/update/deletion anomalies. For most business OLTP databases, 3NF is sufficient. Analytical (OLAP) databases are often intentionally denormalized (star schemas).',
    ex: 'A flat INVOICE table mixing customer info, product info, and invoice header data violates normalization. After 3NF: separate CUSTOMER, PRODUCT, INVOICE, and INVOICE_LINE tables, each about one subject.',
    mk: 'Over-normalizing OLAP databases: star schemas for analytics are deliberately denormalized. Trying to normalize a fact table into 3NF destroys its query performance.',
    src: SD_NORMALIZATION_SRC,
  },
  {
    m: ['first normal form', '1NF', 'repeating groups', 'atomic values'],
    d: '«First Normal Form (1NF)»: all key attributes are defined, there are no repeating groups (each cell holds exactly one atomic value), and all attributes are dependent on the primary key. A «repeating group» is a set of multiple entries of the same type for a single key value.',
    how: 'To convert to 1NF: (1) Eliminate repeating groups; (2) Identify the PK; (3) Identify all functional dependencies. After 1NF: you may still have partial dependencies (common when PK is composite).',
    ex: 'INVOICE table with columns Item1, Item2, Item3 has a repeating group. Fix: create INVOICE_LINE(InvoiceID FK, LineNo, ProductID, Qty, Price) where each row is one line item—no repeating groups.',
    mk: 'Thinking 1NF is "just having a PK": 1NF requires atomic values too. A column storing comma-separated phone numbers ("555-1234, 555-5678") violates 1NF even if there\'s a PK.',
    src: SD_NORMALIZATION_SRC,
  },
  {
    m: ['second normal form', '2NF', 'partial dependency'],
    d: '«Second Normal Form (2NF)»: the table is in 1NF AND has no partial dependencies—every non-key attribute is fully functionally dependent on the entire primary key, not just part of it. A «partial dependency» exists only when the PK is composite.',
    how: 'To convert 1NF → 2NF: (1) Identify partial dependencies (non-key attribute determined by only part of the composite PK); (2) Create new tables for each partial dependency, moving the partial-key and its dependents; (3) Keep the full-key table for attributes that depend on the entire PK. If the PK has a single attribute, the table is automatically in 2NF.',
    ex: 'INVOICE_LINE(InvoiceID, ProductID, Qty, ProductName, ProductPrice): ProductName and ProductPrice depend only on ProductID (partial dependency). Fix: extract PRODUCT(ProductID PK, ProductName, ProductPrice); leave INVOICE_LINE(InvoiceID FK, ProductID FK, Qty).',
    mk: 'Applying 2NF to single-attribute PKs: partial dependency can only exist with a composite PK. A table with a single-column PK is always in 2NF if it\'s in 1NF.',
    src: SD_NORMALIZATION_SRC,
  },
  {
    m: ['third normal form', '3NF', 'transitive dependency'],
    d: '«Third Normal Form (3NF)»: the table is in 2NF AND contains no transitive dependencies—no non-key attribute determines another non-key attribute. A «transitive dependency» exists when A → B → C (A is the PK, B and C are non-key, and B → C).',
    how: 'To convert 2NF → 3NF: (1) Identify transitive dependencies among non-prime attributes; (2) Create new tables to eliminate them, moving the determinant and its dependents; (3) Leave a FK to the new table in the original. Transitive dependencies are harder to spot than partial dependencies—they occur entirely among non-key attributes.',
    ex: 'EMPLOYEE(EmpID PK, DeptID, DeptName, DeptLocation): DeptID → DeptName and DeptID → DeptLocation (transitive through DeptID). Fix: DEPARTMENT(DeptID PK, DeptName, DeptLocation); EMPLOYEE(EmpID PK, DeptID FK).',
    mk: 'Missing transitive dependencies when DeptID looks like a key: DeptID is a non-prime attribute in EMPLOYEE (not part of EmpID PK), so DeptID → DeptName is a transitive dependency—not a partial one.',
    src: SD_NORMALIZATION_SRC,
  },
  {
    m: ['BCNF', 'Boyce-Codd normal form', 'higher normal forms', '4NF', '5NF'],
    d: '«BCNF (Boyce-Codd Normal Form)»: the table is in 3NF AND every determinant is a candidate key. BCNF is a stricter special case of 3NF, only violated when a table has multiple overlapping candidate keys. «4NF» eliminates independent multivalued dependencies; «5NF» eliminates join dependencies. For most business databases, 3NF is sufficient.',
    how: 'BCNF can only be violated when: (1) the table has more than one candidate key, AND (2) those candidate keys are composite and overlapping. When the table contains only one candidate key, 3NF = BCNF. 4NF and 5NF are rarely encountered in practice and are mainly of theoretical interest.',
    ex: 'COURSE_TEACHER(CourseID, TeacherID, TextbookID) where {CourseID, TeacherID} and {CourseID, TextbookID} are both candidate keys: TeacherID → TextbookID violates BCNF because TeacherID alone is not a candidate key.',
    mk: 'Thinking BCNF is always stricter than 3NF in practice: they differ only in tables with multiple overlapping candidate keys, which is uncommon in most business schemas.',
    src: SD_NORMALIZATION_SRC,
  },

  // ── sd-bi-datawarehouse ───────────────────────────────────────────────────

  {
    m: ['business intelligence', 'BI framework', 'BI architecture', 'KPI', 'DSS'],
    d: '«Business Intelligence (BI)» is a comprehensive, cohesive set of tools and processes that «transforms data into information, information into knowledge, and knowledge into wisdom» to support organizational decision-making. A «DSS (Decision Support System)» is a narrower BI tool. Key architecture components include KPIs, master data management, and reporting/alerting/analytics layers.',
    how: 'BI cycle: operational systems generate data → ETL into the data warehouse → analysts query and visualize → decisions are made → outcomes generate new operational data. BI provides: integrating architecture, common user interface, single version of company data, improved organizational performance.',
    ex: 'A retail chain\'s BI system pulls daily POS transactions (operational), loads them into a data warehouse nightly (ETL), and surfaces a KPI dashboard showing regional sales vs. targets to district managers each morning.',
    mk: 'Treating BI as just reporting: modern BI includes advanced analytics, predictive modeling, and real-time alerting—not only historical reports.',
    src: SD_BI_DW_SRC,
  },
  {
    m: ['operational data vs decision support data', 'OLTP vs OLAP data', 'time span granularity dimensionality'],
    d: 'Operational data captures daily business transactions (current, detailed, volatile). «Decision support data» gives tactical/strategic meaning to operational data—it differs in three ways: longer «time span» (years vs. days), coarser «granularity» (aggregated vs. row-level), and higher «dimensionality» (multiple analytical perspectives vs. single-transaction focus).',
    how: 'Operational (OLTP) DBs are optimized for fast single-row inserts/updates (normalized). Decision-support (OLAP) DBs are optimized for complex aggregated queries across millions of rows (denormalized). The ETL process transforms operational data into decision-support data: cleaning, aggregating, and loading into the warehouse.',
    ex: 'OLTP: INSERT into ORDERS one row per sale, current date. OLAP: SELECT SUM(Revenue), Region, Quarter FROM FACT_SALES GROUP BY Region, Quarter—aggregating 3 years of history across millions of rows.',
    mk: 'Running BI analytics directly on the operational database: complex analytical queries will degrade transaction performance. Separation (data warehouse) exists for this reason.',
    src: SD_BI_DW_SRC,
  },
  {
    m: ['data warehouse', 'ISNV', 'integrated subject-oriented time-variant nonvolatile', 'ETL', 'data mart'],
    d: 'A «data warehouse» is an «integrated», «subject-oriented», «time-variant», and «nonvolatile» collection of data for decision support. Integrated: consistent formats/codes across sources. Subject-oriented: organized by major business subjects (Sales, Customer, Product) not operational processes. Time-variant: contains historical data (years). Nonvolatile: data is loaded and read; rarely updated in-place.',
    how: 'ETL (Extract, Transform, Load): extract data from operational sources, transform (clean, standardize, aggregate), load into the warehouse. A «data mart» is a small, single-subject subset of the warehouse serving one department—lower cost and shorter implementation than a full warehouse.',
    ex: 'A retailer\'s warehouse integrates data from the POS system (sales), ERP (inventory), and CRM (customers), transforms regional codes to a standard format, and preserves every transaction for 5 years—nonvolatile, time-variant.',
    mk: 'Calling a normalized operational database a "data warehouse": true data warehouses are subject-oriented and denormalized (often star schemas), not normalized transactional databases.',
    src: SD_BI_DW_SRC,
  },
  {
    m: ['star schema', 'fact table', 'dimension table', 'snowflake schema', 'slice and dice'],
    d: 'A «star schema» maps multidimensional decision-support data into relational tables: a central «fact table» holds numeric measures («facts») with foreign keys to surrounding «dimension tables» that provide descriptive context. Fact table PK = composite of all dimension FKs. «Snowflake schema» normalizes dimension tables into sub-dimensions.',
    how: 'Fact table: each row is one measurable event (a sale, a shipment). Dimensions: Time, Customer, Product, Region—used to filter, group, and label facts. Attributes within dimensions support «slice and dice» (focus on one value) and drill-down/roll-up (year → quarter → month → day hierarchy). Star schema joins are fast because fact tables are denormalized.',
    ex: 'FACT_SALES(TimeID FK, CustomerID FK, ProductID FK, StoreID FK, Revenue, Units). Surrounding dimensions: DIM_TIME(TimeID, Day, Month, Quarter, Year), DIM_PRODUCT(ProductID, Name, Category, Brand), etc.',
    mk: 'Putting descriptive attributes in the fact table: dimension attributes (ProductName, Region) belong in dimension tables, not the fact table, which should contain only measures and dimension FKs.',
    src: SD_BI_DW_SRC,
  },
  {
    m: ['OLAP', 'online analytical processing', 'ROLAP', 'MOLAP', 'multidimensional analysis'],
    d: '«OLAP (Online Analytical Processing)» is a BI style characterized by multidimensional data analysis, advanced database support, and easy-to-use interfaces. «ROLAP (Relational OLAP)» stores multidimensional data in a relational database (star schema) and extends SQL. «MOLAP (Multidimensional OLAP)» stores data in a proprietary cube structure optimized for fast aggregation.',
    how: 'OLAP enables: aggregation (SUM, AVG across dimensions), drill-down (year → month → day), roll-up (day → month → year), slice (filter one dimension), and dice (filter multiple dimensions). ROLAP scales to VLDBs and uses SQL; MOLAP has faster query response but limited scale and proprietary data structures.',
    ex: 'An OLAP cube for retail: dimensions are Time, Product, and Store. A manager can drill down from total annual sales → Q4 → December → Week 52, or slice to just the "Electronics" product category.',
    mk: 'Confusing OLAP with BI: OLAP is one analytical technique within the broader BI framework. BI also includes data mining, dashboards, and reporting tools not specific to dimensional analysis.',
    src: SD_BI_DW_SRC,
  },

  // ── sd-sql-fundamentals ───────────────────────────────────────────────────

  {
    m: ['SQL language categories', 'DML DDL TCL DCL', 'data manipulation language', 'data definition language'],
    d: 'SQL commands fall into four categories: «DML (Data Manipulation Language)»—SELECT, INSERT, UPDATE, DELETE; «DDL (Data Definition Language)»—CREATE TABLE, ALTER TABLE, DROP TABLE, CREATE INDEX; «TCL (Transaction Control Language)»—COMMIT, ROLLBACK, SAVEPOINT; «DCL (Data Control Language)»—GRANT, REVOKE.',
    how: 'DML manipulates data rows. DDL defines schema structure. TCL manages atomic units of work (transactions). DCL controls user permissions. SQL is a nonprocedural language: you declare what you want, not how to retrieve it. The DBMS optimizer determines the execution plan.',
    ex: 'CREATE TABLE CUSTOMER (CustID NUMBER PK, Name VARCHAR2(50))—DDL. INSERT INTO CUSTOMER VALUES (1, \'Alice\')—DML. COMMIT—TCL. GRANT SELECT ON CUSTOMER TO analyst_role—DCL.',
    mk: 'Thinking SQL is only for querying: DDL creates/modifies schema objects; DCL manages security. Knowing all four categories is essential for database administration.',
    src: SD_SQL_FUND_SRC,
  },
  {
    m: ['SELECT statement structure', 'SELECT FROM WHERE GROUP BY HAVING ORDER BY', 'SELECT clauses'],
    d: 'A SELECT query has six clauses (in syntax order): «SELECT» (which columns), «FROM» (which table(s)), «WHERE» (row filter), «GROUP BY» (grouping rows), «HAVING» (group filter), «ORDER BY» (sort). Recommended build order: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY.',
    how: 'FROM defines what data is available. WHERE filters individual rows before grouping. GROUP BY groups filtered rows. HAVING filters the groups. SELECT projects the output columns (aggregate functions here). ORDER BY sorts the final result. WHERE runs before aggregation; HAVING runs after.',
    ex: 'SELECT Region, SUM(Revenue) AS TotalRev FROM SALES WHERE Year = 2025 GROUP BY Region HAVING SUM(Revenue) > 1000000 ORDER BY TotalRev DESC; — returns only regions with >$1M revenue in 2025, sorted descending.',
    mk: 'Using WHERE to filter aggregate results: WHERE cannot reference aggregate function output. Use HAVING instead—it operates on the grouped result set.',
    src: SD_SQL_FUND_SRC,
  },
  {
    m: ['WHERE clause', 'comparison operators SQL', 'logical operators AND OR NOT', 'BETWEEN IN LIKE IS NULL'],
    d: 'The WHERE clause filters rows using «comparison operators» (=, <, <=, >, >=, <> or !=) and «logical operators» (AND, OR, NOT). «Special operators»: BETWEEN (range check), IN (membership in a list), LIKE (pattern match with % and _), IS NULL (null check).',
    how: 'AND has higher precedence than OR—use parentheses to avoid ambiguity. LIKE: % matches any sequence of characters; _ matches exactly one character. IS NULL is the correct test for null (= NULL never evaluates true). IN is shorthand for multiple OR equality conditions.',
    ex: "WHERE Price BETWEEN 10 AND 50 AND Category IN ('Books','Electronics') AND Name LIKE 'A%' AND DiscountCode IS NULL — rows where price is 10–50, category is Books or Electronics, name starts with A, and no discount code.",
    mk: "Using = NULL instead of IS NULL: NULL = NULL returns UNKNOWN (not TRUE) in SQL's three-valued logic. Always use IS NULL or IS NOT NULL to test for null values.",
    src: SD_SQL_FUND_SRC,
  },
  {
    m: ['ORDER BY', 'DISTINCT', 'sort SQL', 'unique values SQL'],
    d: '«ORDER BY» sorts the final query result by one or more columns, in ASC (default) or DESC order. «DISTINCT» eliminates duplicate rows from the result set, returning only unique values in the specified column(s).',
    how: 'ORDER BY comes last in the logical query sequence—it sorts the already-filtered and projected result. Multiple sort keys: ORDER BY Region ASC, Revenue DESC (primary sort Region, secondary Revenue). DISTINCT applies to the entire selected column list, not individual columns.',
    ex: 'SELECT DISTINCT Category FROM PRODUCT ORDER BY Category ASC; — returns each unique product category, alphabetically sorted.',
    mk: 'Confusing DISTINCT with GROUP BY: DISTINCT removes duplicate rows in the result. GROUP BY groups rows for aggregation—two different operations with similar-looking results for simple cases.',
    src: SD_SQL_FUND_SRC,
  },
  {
    m: ['column alias', 'computed column', 'rules of precedence SQL', 'arithmetic operators SQL'],
    d: 'A «column alias» (AS keyword) gives a column or computed expression an alternative display name. A «computed column» derives its value via arithmetic (P_PRICE * 1.07) or functions—it does not need to be stored. Arithmetic follows «rules of precedence»: parentheses first, then multiplication/division, then addition/subtraction.',
    how: 'Aliases simplify output headers and can be referenced in ORDER BY (but not WHERE in most databases). Computed columns allow on-the-fly calculations without adding stored columns. Date arithmetic: subtract two DATE values to get days elapsed.',
    ex: "SELECT P_DESCRIPT, P_PRICE, P_PRICE * 1.07 AS PriceWithTax FROM PRODUCT WHERE P_PRICE * 1.07 < 50;",
    mk: "Using an alias in the WHERE clause: aliases defined in SELECT are not yet available when WHERE is evaluated (WHERE runs first). Repeat the expression in WHERE or use a subquery.",
    src: SD_SQL_FUND_SRC,
  },

  // ── sd-sql-joins-agg ──────────────────────────────────────────────────────

  {
    m: ['INNER JOIN', 'JOIN ON', 'JOIN USING', 'natural join', 'join SQL'],
    d: 'An «INNER JOIN» returns only rows with matching values in both tables on the join condition—unmatched rows from either table are excluded. «JOIN ON» specifies the exact join condition; «JOIN USING» specifies the common column name; «NATURAL JOIN» auto-detects common columns by matching names and types.',
    how: 'Syntax: SELECT cols FROM A INNER JOIN B ON A.id = B.id. Old-style: SELECT cols FROM A, B WHERE A.id = B.id—functionally equivalent but less readable and prone to accidental cross joins. A CROSS JOIN (no ON clause) returns the Cartesian product (every row from A × every row from B).',
    ex: "SELECT C.CustName, O.OrderDate FROM CUSTOMER C INNER JOIN ORDERS O ON C.CustID = O.CustID; — returns only customers who have at least one order.",
    mk: "Forgetting the ON condition in an old-style join: SELECT * FROM A, B without a WHERE join condition produces a cross join (Cartesian product), which can return millions of unexpected rows.",
    src: SD_SQL_JOINS_SRC,
  },
  {
    m: ['OUTER JOIN', 'LEFT OUTER JOIN', 'RIGHT OUTER JOIN', 'FULL OUTER JOIN', 'unmatched rows'],
    d: 'An «OUTER JOIN» returns matched rows plus «unmatched rows» from one or both tables, filling unmatched sides with NULL. «LEFT OUTER JOIN»: all rows from the left table + matched right. «RIGHT OUTER JOIN»: all rows from the right table + matched left. «FULL OUTER JOIN»: all rows from both tables.',
    how: 'Use outer joins when you need to see rows that have no matching partner—e.g., customers with no orders (LEFT JOIN CUSTOMER to ORDERS). The unmatched side\'s columns appear as NULL. RIGHT JOIN can usually be rewritten as a LEFT JOIN by swapping table order.',
    ex: "SELECT C.CustName, O.OrderID FROM CUSTOMER C LEFT OUTER JOIN ORDERS O ON C.CustID = O.CustID; — returns ALL customers; OrderID is NULL for customers with no orders.",
    mk: "Using INNER JOIN when you need all rows from one side: INNER JOIN silently drops unmatched rows. If you expect nulls in the result for unmatched cases, use an OUTER JOIN.",
    src: SD_SQL_JOINS_SRC,
  },
  {
    m: ['aggregate functions SQL', 'COUNT MIN MAX SUM AVG', 'aggregate processing'],
    d: '«Aggregate functions» collapse multiple rows into a single summary value: «COUNT» (number of non-null values), «MIN» (minimum), «MAX» (maximum), «SUM» (total), «AVG» (arithmetic mean). COUNT(*) counts all rows including nulls; COUNT(column) counts non-null values only.',
    how: 'Aggregate functions are used in the SELECT list or HAVING clause—never in WHERE. They operate on the set of rows defined by GROUP BY (or all rows if no GROUP BY). NULL values are ignored by SUM, AVG, MIN, MAX; COUNT(column) also ignores NULLs, but COUNT(*) does not.',
    ex: "SELECT COUNT(*) AS TotalOrders, SUM(Amount) AS TotalRevenue, AVG(Amount) AS AvgOrder, MIN(Amount), MAX(Amount) FROM ORDERS WHERE Year = 2025;",
    mk: "Putting an aggregate function in a WHERE clause: WHERE executes before aggregation, so you can't filter on COUNT or SUM there. Move aggregate conditions to HAVING.",
    src: SD_SQL_JOINS_SRC,
  },
  {
    m: ['GROUP BY clause', 'grouping data SQL', 'frequency distribution SQL'],
    d: '«GROUP BY» creates groups of rows that share the same values in the specified column(s), enabling aggregate functions to operate per-group rather than on the whole table. Every column in the SELECT list must either be in the GROUP BY clause or be wrapped in an aggregate function.',
    how: 'Logical execution: FROM → WHERE → GROUP BY (groups formed) → HAVING (groups filtered) → SELECT (aggregates computed) → ORDER BY. Multiple grouping columns create a hierarchy: GROUP BY Region, Product groups by each Region-Product combination.',
    ex: "SELECT Region, Product, SUM(Units) FROM SALES GROUP BY Region, Product ORDER BY Region; — one row per Region-Product combination showing total units sold.",
    mk: "Selecting a non-aggregated, non-grouped column: SELECT Region, SalesPerson, SUM(Revenue) FROM SALES GROUP BY Region will fail—SalesPerson is neither grouped nor aggregated. Either add it to GROUP BY or apply an aggregate (MAX(SalesPerson)).",
    src: SD_SQL_JOINS_SRC,
  },
  {
    m: ['HAVING clause', 'filter groups SQL'],
    d: 'The «HAVING clause» filters groups produced by GROUP BY, applying conditions to aggregate function results. It is analogous to WHERE but operates after grouping—WHERE filters rows before grouping, HAVING filters groups after aggregation.',
    how: 'HAVING can reference aggregate functions (HAVING SUM(Revenue) > 1000) and grouping columns. WHERE cannot reference aggregates. A query can have both WHERE (pre-aggregation row filter) and HAVING (post-aggregation group filter) simultaneously.',
    ex: "SELECT DeptID, COUNT(*) AS Headcount, AVG(Salary) AS AvgSal FROM EMPLOYEE WHERE Status = 'Active' GROUP BY DeptID HAVING COUNT(*) > 5 AND AVG(Salary) > 60000; — active departments with more than 5 employees averaging over $60K.",
    mk: "Writing WHERE AVG(Salary) > 60000: this is a syntax error—AVG is not evaluated until after GROUP BY. The condition on the aggregate must go in HAVING.",
    src: SD_SQL_JOINS_SRC,
  },

  // ── sd-sql-advanced ───────────────────────────────────────────────────────

  {
    m: ['subquery SQL', 'nested query', 'inner query outer query', 'WHERE subquery', 'IN subquery', 'HAVING subquery'],
    d: 'A «subquery» (nested query) is a SELECT statement inside another SQL statement. The «inner query» executes first; its output becomes the input for the «outer query». Subqueries can return a single value (scalar), a list of values (used with IN/ANY/ALL), or a virtual table (used in FROM).',
    how: 'Three common placements: (1) WHERE subquery: filters outer rows based on the inner result (e.g., WHERE Price > (SELECT AVG(Price) FROM PRODUCT)); (2) IN subquery: checks membership in a dynamically derived list; (3) FROM subquery: treats the inner result as a derived table (inline view); (4) Attribute-list subquery: computes a scalar value per outer row.',
    ex: "SELECT ProdName, Price FROM PRODUCT WHERE Price > (SELECT AVG(Price) FROM PRODUCT); — list products above average price using a scalar subquery.",
    mk: "Using a multi-row subquery with = instead of IN: SELECT * FROM PRODUCT WHERE P_CODE = (SELECT P_CODE FROM ORDER_LINE) fails if the inner query returns more than one row. Use IN for multi-row subqueries.",
    src: SD_SQL_ADV_SRC,
  },
  {
    m: ['correlated subquery', 'EXISTS operator', 'ALL ANY operators'],
    d: 'A «correlated subquery» executes once per row of the outer query—the inner query references a column from the outer query, making it dependent. «EXISTS» returns TRUE if the subquery returns at least one row. «ALL» compares a value against every result of a subquery (all must match); «ANY» requires just one match.',
    how: 'Correlated subqueries are powerful but expensive—they can run millions of times for large outer result sets. EXISTS is often faster than IN for correlated checks because it short-circuits on the first match. NOT EXISTS identifies rows with no matching subquery result (useful for anti-join patterns).',
    ex: "SELECT C.CustName FROM CUSTOMER C WHERE EXISTS (SELECT 1 FROM ORDERS O WHERE O.CustID = C.CustID AND O.Year = 2025); — customers who placed at least one order in 2025.",
    mk: "Confusing IN with EXISTS for correlated logic: IN passes a static list; EXISTS executes once per outer row and short-circuits. EXISTS is generally preferred for correlated subqueries when performance matters.",
    src: SD_SQL_ADV_SRC,
  },
  {
    m: ['SQL functions', 'date functions SQL', 'numeric functions SQL', 'string functions SQL', 'conversion functions SQL'],
    d: 'SQL provides built-in function categories: «date/time functions» (SYSDATE, ADD_MONTHS, MONTHS_BETWEEN, TRUNC for dates), «numeric functions» (ROUND, TRUNC, MOD, ABS, POWER), «string functions» (UPPER, LOWER, SUBSTR, LENGTH, TRIM, CONCAT), and «conversion functions» (TO_CHAR, TO_DATE, TO_NUMBER) to change data types.',
    how: 'Functions appear in SELECT list, WHERE clause, or ORDER BY. Date arithmetic: SYSDATE - HireDate gives days of service. String functions enable cleaning and formatting (UPPER for case-insensitive comparison). Conversion functions allow storing a date as a character string or formatting a number as currency.',
    ex: "SELECT EmpID, UPPER(LastName), ROUND(Salary/12, 2) AS MonthlySal, TO_CHAR(HireDate, 'Month DD, YYYY') FROM EMPLOYEE WHERE MONTHS_BETWEEN(SYSDATE, HireDate) > 60;",
    mk: "Applying string functions to numeric columns without conversion: SUBSTR(12345, 2, 3) requires the number to be treated as a character—use TO_CHAR(12345) first.",
    src: SD_SQL_ADV_SRC,
  },
  {
    m: ['set operators SQL', 'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT', 'MINUS'],
    d: '«Set operators» combine results of two SELECT queries: «UNION» merges results eliminating duplicates; «UNION ALL» merges including duplicates; «INTERSECT» returns only rows appearing in both result sets; «EXCEPT» (Oracle: MINUS) returns rows in the first result that are not in the second.',
    how: 'Requirements: both queries must select the same number of columns with compatible data types. Column names come from the first query. Order of results is not guaranteed without ORDER BY on the outer statement. UNION ALL is faster than UNION (no dedup step); use it when duplicates are acceptable.',
    ex: "SELECT CustID FROM ACTIVE_CUSTOMERS UNION SELECT CustID FROM PROSPECT_LIST; — all unique IDs from either list. | SELECT ProductID FROM ORDERED_THIS_YEAR INTERSECT SELECT ProductID FROM ORDERED_LAST_YEAR; — products ordered in both years.",
    mk: "Using UNION when UNION ALL is sufficient: UNION sorts and deduplicates, adding overhead. If duplicates don't matter (or can't occur), UNION ALL is significantly faster.",
    src: SD_SQL_ADV_SRC,
  },
  {
    m: ['crafting SELECT queries', 'build order SQL', 'know your data SQL query design'],
    d: 'Effective query design follows two principles: «Know Your Data» (understand the data model, tables, keys, and data quality) and «Know the Problem» (understand exactly what the question asks). The recommended «clause build order» is: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY—matching the logical execution sequence.',
    how: 'Start with FROM to establish available data. Add WHERE to filter rows early (reduce set size before grouping). Add GROUP BY if aggregation is needed. Add HAVING to filter groups. Write SELECT to project and compute the output. Add ORDER BY last. In real-world databases, always check for nulls, data type mismatches, and unexpected duplicates.',
    ex: "For 'Which sales reps had average deal size above $5K last quarter?': FROM DEALS → WHERE CloseDate BETWEEN q-start AND q-end → GROUP BY RepID → HAVING AVG(DealSize) > 5000 → SELECT RepID, AVG(DealSize) → ORDER BY AVG(DealSize) DESC.",
    mk: "Writing SELECT first then trying to figure out FROM/WHERE: starting from SELECT leads to selecting columns without knowing what's available or what filtering is needed. Always anchor the query with FROM first.",
    src: SD_SQL_ADV_SRC,
  },
];