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

## intent:affirm
- da
- dap
- sigur
- that sounds good
- correct

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

## intent:get_location
- Unde se află [ochelarii](obj)
- Unde e [buletinul](obj)?
- știi unde am pus [cheile](obj)
- poți să-mi zici unde este [încârcătorul de telefon](obj)
- unde am lăsat [ceasul](obj)?

## intent:get_timestamp
- Când [am fost la sala](action)
- De când [începe vacanța](action)
- Până când [trebuie trimisă tema](action)

## intent:store_person_attr
- Mailul lui [Alex Marin](person) este [alex@marin.com](attribute)
- Adresa [Elenei](person) este [strada Zorilor numarul 9](attribute)

## lookup:person
  data/lookup-tables/person.txt
  
## lookup:location
  data/lookup-tables/location.txt