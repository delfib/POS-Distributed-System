# 4/12

Por ahora, añadimos los Point of Sale, en donde cada uno tiene su propio deposito de articulos con su base de datos local.
Implementamos tambien el cliente, que puede comprar productos.

Hay que implementar el algoritmo de eleccion de lider

Hay que ver bien todavia que arquitectura vamos a usar.

## DUDAS

- que operaciones deberian tener permitidos los nodos y cuales no? Los nodos solamente deberian poder vender o agregar productos nuevos por ejemplo? O esto es solo algo que pueda hacer el nodo lider?
- Como deberia darse la comunicacion entre los nodos? con un address con puerto?

---

## Implementation

- Arquitectura peer-to-peer?
- Topologia: Mesh

## Coordinacion

- El leader es el unico en enviar mensajes -> actualiza el precio de los followers
- Elección: ?????

## Replicación y Distribución

## Tolerancia a fallas

- Concenso: RAFT ???
