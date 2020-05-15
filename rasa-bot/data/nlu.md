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
- Memo

## intent:store_location
- cartea e [pe masă](location)
- Cardul de debit este [în portofelul vechi](location)
- buletinul meu se află [în rucsac](location)
- Am pus foile cu tema la mate [pe dulapul din sufragerie](location)
- Alex stă [în căminul P5](location)
- Maria Popescu locuiește [pe Bulevardul Timișoara numărul 5](location)
- Bonurile de transport sunt [în plicul de pe raft](location)
- cardul de memorie e [sub cutia telefonului](location)

## intent:get_location
- [Unde](query_word_loc) se află ochelarii
- [Unde](query_word_loc) e buletinul?
- știi [unde](query_word_loc) am pus cheile
- poți să-mi zici [unde](query_word_loc) este încârcătorul de telefon
- [unde](query_word_loc) am lăsat ceasul?
- [pe unde](query_word_loc) e sticla de ulei
- [de unde](query_word_loc) am cumpărat uscătorul de păr
- [până unde](query_word_loc) a alergat aseară Marius?

## intent:store_attr
- Mailul lui [Alex](person) Marin este alex@marin.com
- Adresa [Elenei](owner) este strada Zorilor numărul 9
- Numărul de telefon al lui [Dan](person) e 123456789
- numărul blocului [fratelui Mihaelei](owner) e 10
- anul nașterii lui [Ștefan](person) cel Mare a fost 1433
- numele [meu](owner) este Gabriel
- cheile [mele](owner) de la casă sunt ușoare
- adresa de la serviciu este Bulevardul Unirii nr. 0

## intent:get_attr
- [Care e](query_word_spec) mailul attribute lui [Mihai](person)?
- [care este](query_word_spec) numele de utilizator de github [al laborantului de EIM](owner)
- poți să-mi spui [care era](query_word_spec) prețul [abonamentului la sală](owner)
- zi-mi [care a fost](query_word_spec) câștigătorul concursului Eestec Olympics de anul trecut
- [care e](query_word_spec) adresa colegului meu?
- [care era](query_word_spec) denumirea bazei de date de la proiect?
- [care sunt](query_word_spec) tipurile de rețele neurale
- [Care este](query_word_spec) valoarea de adevăr a propoziției
- [care e](query_word_spec) frecvența procesorului meu

## intent:get_timestamp
- zi-mi [când](query_word_time) [am fost la sală](action)?
- [De când](query_word_time) [începe vacanța](action)
- [Până când](query_word_time) [trebuie trimisă tema](action)
- [cât timp](query_word_time) [a durat prezentarea temei](action)
- [peste cât timp](query_word_time) se termină starea de urgență?
- peste [câte](query_word_time) zile [începe sesiunea de examene](action)
- [Când](query_word_time) am avut ultimul examen anul trecut?
- [când](query_word_time) vor avea loc alegerile locale din 2020

## intent:get_specifier
- [care](query_word_spec) student a terminat primul tema
- [la ce](query_word_spec) apartament locuiește verișorul meu
- [ce fel de](query_word_spec) imprimantă am acasă
- [în care](query_word_spec) dulap am pus dosarul
- [ce](query_word_spec) examene vor fi date în iunie?
- [despre ce](query_word_spec) operație s-a vorbit
- [de la care](query_word_spec) prieten e cadoul acesta
- [pentru ce](query_word_spec) test am învățat acum 2 zile
- [pe care](query_word_spec) masă am lăsat ieri periuța de dinți?
- [care](query_word_spec) fotbalist a fost dat afară săptămâna trecută
- [ce](query_word_spec) floare s-a uscat

## intent:get_subject
- [Cine](query_word_subj) [stă în căminul P16](action)?
- Spune-mi te rog [cine](query_word_subj) [a inventat becul](action)
- [cine](query_word_subj) [a câștigat locul 1 la olimpiada națională de matematică din 2016](action)
- [cine](query_word_subj) [m-a tuns ultima dată](action)?

  
## lookup:query_word_loc
  data/lookup-tables/query-word-loc.txt
  
## lookup:query_word_time
  data/lookup-tables/query-word-time.txt
  
## lookup:query_word_spec
  data/lookup-tables/query-word-spec.txt

## lookup:person
  data/lookup-tables/person.txt