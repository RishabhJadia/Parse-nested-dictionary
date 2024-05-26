package main

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"

	_ "movie_crud_api/docs" // Replace with the actual import path of your project

	"github.com/gorilla/mux"
	httpSwagger "github.com/swaggo/http-swagger"
)

// @title Item API
// @version 1.0
// @description This is a sample server for items.
// @host localhost:8000
// @BasePath /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization

// Item represents an item
type Item struct {
	ID    string  `json:"id" example:"1"`
	Name  string  `json:"name" example:"Item One"`
	Price float64 `json:"price" example:"10.00"`
}

var items []Item

// Middleware function to check for the Bearer token
func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		log.Printf("Authorization Header: %s", authHeader)
		if authHeader == "" {
			http.Error(w, "Authorization header is required", http.StatusUnauthorized)
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, "Invalid authorization header format", http.StatusUnauthorized)
			return
		}

		token := parts[1]
		// Here you would typically validate the token. For simplicity, we're just checking if it's non-empty.
		if token == "" {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		// If token is valid, proceed to the next handler
		next.ServeHTTP(w, r)
	})
}

// @Summary Get all items
// @Description Get all items
// @Tags items
// @Accept  json
// @Produce  json
// @Success 200 {array} Item
// @Security BearerAuth
// @Router /items [get]
func getItems(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(items)
}

// @Summary Get an item by ID
// @Description Get an item by ID
// @Tags items
// @Accept  json
// @Produce  json
// @Param id path string true "Item ID"
// @Success 200 {object} Item
// @Failure 404 {object} map[string]string
// @Security BearerAuth
// @Router /items/{id} [get]
func getItem(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for _, item := range items {
		if item.ID == params["id"] {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{"message": "Item not found"})
}

// @Summary Create a new item
// @Description Create a new item
// @Tags items
// @Accept  json
// @Produce  json
// @Param item body Item true "New Item"
// @Success 201 {object} Item
// @Security BearerAuth
// @Router /items [post]
func createItem(w http.ResponseWriter, r *http.Request) {
	var newItem Item
	json.NewDecoder(r.Body).Decode(&newItem)
	items = append(items, newItem)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(newItem)
}

// @Summary Update an item
// @Description Update an item
// @Tags items
// @Accept  json
// @Produce  json
// @Param id path string true "Item ID"
// @Param item body Item true "Updated Item"
// @Success 200 {object} Item
// @Failure 404 {object} map[string]string
// @Security BearerAuth
// @Router /items/{id} [put]
func updateItem(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for i, item := range items {
		if item.ID == params["id"] {
			items = append(items[:i], items[i+1:]...)
			var updatedItem Item
			json.NewDecoder(r.Body).Decode(&updatedItem)
			updatedItem.ID = params["id"]
			items = append(items, updatedItem)
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(updatedItem)
			return
		}
	}
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{"message": "Item not found"})
}

// @Summary Delete an item
// @Description Delete an item
// @Tags items
// @Accept  json
// @Produce  json
// @Param id path string true "Item ID"
// @Success 200 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Security BearerAuth
// @Router /items/{id} [delete]
func deleteItem(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for i, item := range items {
		if item.ID == params["id"] {
			items = append(items[:i], items[i+1:]...)
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]string{"message": "Item deleted"})
			return
		}
	}
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{"message": "Item not found"})
}

func main() {
	r := mux.NewRouter()

	// Sample data
	items = append(items, Item{ID: "1", Name: "Item One", Price: 10.00})
	items = append(items, Item{ID: "2", Name: "Item Two", Price: 20.00})

	// Subrouter for API routes that require authentication
	api := r.PathPrefix("/").Subrouter()
	api.Use(authMiddleware)
	api.HandleFunc("/items", getItems).Methods("GET")
	api.HandleFunc("/items/{id}", getItem).Methods("GET")
	api.HandleFunc("/items", createItem).Methods("POST")
	api.HandleFunc("/items/{id}", updateItem).Methods("PUT")
	api.HandleFunc("/items/{id}", deleteItem).Methods("DELETE")

	// Swagger documentation endpoint (no authentication)
	r.PathPrefix("/swagger/").Handler(httpSwagger.WrapHandler)

	log.Println("Server started on :8000")
	log.Fatal(http.ListenAndServe(":8000", r))
}
