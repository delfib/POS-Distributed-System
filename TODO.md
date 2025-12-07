# TODO for project

## List

### Terminar los handlers en POS

### Pasar bien los comportamientos de transaction manager [dELFI]
(
    - En el sell_product(), si el cliente quiere comprar 5 manzanas y el POS tiene solo 3, no va a vender 3 y pedirle a otro peer que venda 2, un unico nodo vende todo o no vende nada. Ver si esta bien esta implementacion.
)

### Implementar concensus (Leader Election) [AGUSTIN]

### Implementar el update de precios para todos los nodos [DELFI]
(
    - implemente un update muy sencillo, nada de RAFT ni 2FC. Cuando el leader recive un update price, actualiza el suyo y depsues manda un broadcast a todos los demas nodos. cada uno que recibe ese mensaje debera actualizar su propio precio. si un nodo no puede hacer el update por alguna razon, no lo va a hacer.
    - Otra cosa, si el update price se hace sobre un nodo que no es lider, ese nodo no le reenvia el request al lider, simpemente tira error. deberia poder el nodo reenviarle el request al lider para que este lo pueda hacer?
)


### Si pinta hacer un menu con operaciones para el cliente [AGUSTIN]

### Terminar PeerManager
