// https://www.youtube.com/watch?v=yyUHQIec83I
package main

import "fmt"

func main() {
	// type 1 declaration of type
	// var conferenceName = "Go Conference" // I want to use this words in many places
	// const conferenceTickets = 50         // constants are like variables, but their values cannot be changed
	// var remainingTickets = 50

	// type 2 declaration of type
	// var conferenceName string = "Go Conference" // I want to use this words in many places
	// const conferenceTickets int = 50            // constants are like variables, but their values cannot be changed
	// var remainingTickets int = 50

	// type 3 declaration of type shorthand
	conferenceName := "Go Conference" // I want to use this words in many places
	const conferenceTickets int = 50  // constants are like variables, but their values cannot be changed
	var remainingTickets uint = 50
	// type 1 of printing
	// fmt.Println("Welcome to our", conferenceName, "booking application")
	// fmt.Println("We have total of", conferenceTickets, "tickets and", remainingTickets, "are still available")
	// fmt.Println("Get your tickets here to attend")

	// type 2 of printing
	// formatted output
	fmt.Printf("conferenceTickets is %T, remainingTickets is %T, conferenceName is %T\n", conferenceTickets, remainingTickets, conferenceName)
	fmt.Printf("Welcome to our %v booking application\n", conferenceName)
	fmt.Printf("We have total of %v tickets and %v are still available", conferenceTickets, remainingTickets)
	fmt.Println("Get your tickets here to attend")

	for {
		// Array it required fixed size, only same datatype can be stored
		// disadvantage of array: if we dont know the size of array
		// type 1 of declaration array
		// var bookings = [50]string{}
		// var bookings [50]string  //array
		// type 2 of declaration array
		// slice is an abstraction of array. slice are more flexible and powerful. dynamic in nature i.e., re-sized when needed
		// type 1 declaration of slice
		// var bookings []string //slice
		// type 2 declaration of slice
		// var bookings = []string{} //slice
		// type 3 declaration of slice
		bookings := []string{} //slice

		// Data types
		var firstName string
		var lastName string
		var email string
		var userTickets uint

		// getting user input
		fmt.Println("Enter your firstName: ")
		fmt.Scan(&firstName) //store variable in memory address
		fmt.Println("Enter your lastName: ")
		fmt.Scan(&lastName) //store variable in memory address
		fmt.Println("Enter your email: ")
		fmt.Scan(&email) //store variable in memory address
		fmt.Println("Enter number of tickets: ")
		fmt.Scan(&userTickets) //store variable in memory address

		remainingTickets = remainingTickets - userTickets
		// bookings[0] = firstName + " " + lastName  //array
		bookings = append(bookings, firstName+" "+lastName) //slice
		// fmt.Printf("The whole array: %v\n", bookings)
		// fmt.Printf("The first value: %v\n", bookings[0])
		// fmt.Printf("Array Type: %T\n", bookings)
		// fmt.Printf("Length of Array: %v\n", len(bookings))
		fmt.Printf("The whole slice: %v\n", bookings)
		fmt.Printf("The first value: %v\n", bookings[0])
		fmt.Printf("Slice Type: %T\n", bookings)
		fmt.Printf("Length of Slice: %v\n", len(bookings))
		fmt.Printf("Thank you %v %v for booking %v tickets. You will receive a confirmation email at %v.\n", firstName, lastName, userTickets, email)
		fmt.Printf("%v tickets remaining for %v\n", remainingTickets, conferenceName)

		fmt.Printf("These are all our bookings: %v\n", bookings)
	}
	// // Array it required fixed size, only same datatype can be stored
	// // disadvantage of array: if we dont know the size of array
	// // type 1 of declaration array
	// // var bookings = [50]string{}
	// // var bookings [50]string  //array
	// // type 2 of declaration array
	// // slice is an abstraction of array. slice are more flexible and powerful. dynamic in nature i.e., re-sized when needed
	// // type 1 declaration of slice
	// // var bookings []string //slice
	// // type 2 declaration of slice
	// // var bookings = []string{} //slice
	// // type 3 declaration of slice
	// bookings := []string{} //slice

	// // Data types
	// var firstName string
	// var lastName string
	// var email string
	// var userTickets uint

	// // getting user input
	// fmt.Println("Enter your firstName: ")
	// fmt.Scan(&firstName) //store variable in memory address
	// fmt.Println("Enter your lastName: ")
	// fmt.Scan(&lastName) //store variable in memory address
	// fmt.Println("Enter your email: ")
	// fmt.Scan(&email) //store variable in memory address
	// fmt.Println("Enter number of tickets: ")
	// fmt.Scan(&userTickets) //store variable in memory address

	// remainingTickets = remainingTickets - userTickets
	// // bookings[0] = firstName + " " + lastName  //array
	// bookings = append(bookings, firstName+" "+lastName) //slice
	// // fmt.Printf("The whole array: %v\n", bookings)
	// // fmt.Printf("The first value: %v\n", bookings[0])
	// // fmt.Printf("Array Type: %T\n", bookings)
	// // fmt.Printf("Length of Array: %v\n", len(bookings))
	// fmt.Printf("The whole slice: %v\n", bookings)
	// fmt.Printf("The first value: %v\n", bookings[0])
	// fmt.Printf("Slice Type: %T\n", bookings)
	// fmt.Printf("Length of Slice: %v\n", len(bookings))
	// fmt.Printf("Thank you %v %v for booking %v tickets. You will receive a confirmation email at %v.\n", firstName, lastName, userTickets, email)
	// fmt.Printf("%v tickets remaining for %v\n", remainingTickets, conferenceName)

	// fmt.Printf("These are all our bookings: %v\n", bookings)

}

// package main

// import (
// 	"encoding/json"
// 	"fmt"
// 	"log"
// )

// func main() {
// 	// Define a slice of maps
// 	bookings := make([]map[string]interface{}, 0)

// 	// Data to populate the slice
// 	names := []string{"Alice", "Bob", "Charlie"}
// 	ages := []int{28, 34, 22}

// 	// Dynamically create maps and append to the slice
// 	for i := range names {
// 		booking := map[string]interface{}{
// 			"name": names[i],
// 			"age":  ages[i],
// 		}
// 		bookings = append(bookings, booking)
// 	}
// 	bookingsJSON, err := json.Marshal(bookings)
// 	if err != nil {
// 		log.Fatalf("Error marshalling bookings to JSON: %v", err)
// 	}

// 	// Print the JSON string
// 	fmt.Println(string(bookingsJSON))
// 	// Print the slice of maps
// 	// for i, booking := range bookings {
// 	// 	fmt.Printf("Booking %d: %v\n", i+1, booking)
// 	// }
// }
