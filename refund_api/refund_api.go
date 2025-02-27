package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type RefundRequest struct {
	UserID  int     `json:"user_id"`
	OrderID int  `json:"order_id"`
	Amount  float64 `json:"amount"`
}

type RefundResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

func processRefund(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var request RefundRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	log.Printf("Processing refund for User %d, Order %s, Amount %.2f", request.UserID, request.OrderID, request.Amount)

	response := RefundResponse{
		Status:  "success",
		Message: "Refund processed successfully",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/refund", processRefund)
	log.Println("Refund Processing API is running on port 8080")
	http.ListenAndServe(":8080", nil)
}
