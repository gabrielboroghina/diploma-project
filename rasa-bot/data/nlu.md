## intent:greet
- hey
- hei
- Salut
- bună

## intent:goodbye
- bye
- pa
- pa pa
- mersi
- gata
- super

## intent:affirm
- da
- dap
- sigur
- pare ok
- corect

## intent:deny
- nu
- nope
- nu prea
- clar nu

## intent:store_request
- Vreau să reții ceva
- Poți să reții ceva, te rog?
- Memorează
- Memorează ceva
- Reține ceva
- Ține minte

## intent:store_location
- [cartea](obj) e [pe masă](location)
- [Cardul de debit](obj) este [în portofelul vechi](location)
- [buletinul meu](obj) se află [în rucsac](location)
- Am pus [foile cu tema la mate](obj) [pe dulapul din sufragerie](location)
- Alex stă [în căminul P5](location)
- Maria Popescu locuiește [pe Bulevardul Timișoara numărul 5](location)
- Bonurile de transport sunt [în plicul de pe raft](location)

## intent:store_attr
- [Mailul](attribute) [lui Alex Marin](owner) este alex@marin.com
- [Adresa](attribute) [Elenei](owner) este strada Zorilor numărul 9
- [Numărul de telefon](attribute) [al lui Dan](owner) e 123456789
- [numărul blocului](attribute) [fratelui Mihaelei](owner) e 10
- [anul nașterii](attribute) [lui Ștefan cel Mare](owner) a fost 1433 

## intent:get_attr
- Care e [mailul](attribute) [lui Mihai](owner)
- care este [numele de utilizator de github](attribute) [al laborantului de EIM](owner)
- poți să-mi spui care era [prețul](attribute) [abonamentului la sală](owner)
- zi-mi care a fost [câștigătorul](attribute) [concursului Eestec Olympics de anul trecut](owner)

## intent:get_location
- Unde se află [ochelarii](obj)
- Unde e [buletinul](obj)?
- știi unde am pus [cheile](obj)
- poți să-mi zici unde este [încârcătorul de telefon](obj)
- unde am lăsat [ceasul](obj)?

## intent:get_timestamp
- Când [am fost la sală](action)?
- De când [începe vacanța](action)
- Până când [trebuie trimisă tema](action)
- cât timp [a durat prezentarea temei](action)
- peste câte zile [începe sesiunea de examene](action)

## intent:get_subject
- Cine stă în căminul P16?
- Spune-mi te rog cine a inventat becul
- cine a câștigat locul 1 la olimpiada națională de matematică din 2016

## intent:get_specifier
- care student a terminat primul tema
- la ce apartament locuiește verișorul meu
- ce fel de imprimantă am acasă 


## lookup:person
  data/lookup-tables/person.txt
  
## lookup:location
  data/lookup-tables/location.txt