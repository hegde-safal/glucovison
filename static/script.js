document.addEventListener("DOMContentLoaded", () => {
    const analyzeBtn = document.getElementById("analyze-btn");
    const statusEl = document.getElementById("status");
    const resultsSection = document.getElementById("results");
    const unmatchedSection = document.getElementById("unmatched-section");
    const unmatchedList = document.getElementById("unmatched-list");
  
    const fields = {
      breakfast: document.getElementById("breakfast"),
      lunch: document.getElementById("lunch"),
      snacks: document.getElementById("snacks"),
      dinner: document.getElementById("dinner"),
    };
  
    const resultFields = {
      total_calories: document.getElementById("total_calories"),
      total_carbs: document.getElementById("total_carbs"),
      total_sugar: document.getElementById("total_sugar"),
      total_protein: document.getElementById("total_protein"),
      total_fat: document.getElementById("total_fat"),
      total_fiber: document.getElementById("total_fiber"),
    };
  
    function setStatus(message, isError = false) {
      statusEl.textContent = message || "";
      statusEl.classList.toggle("error", Boolean(isError));
    }
  
    async function analyzeMeals() {
      setStatus("Analyzing meals...", false);
      resultsSection.classList.add("hidden");
      unmatchedSection.classList.add("hidden");
      unmatchedList.innerHTML = "";
  
      const payload = {
        breakfast: fields.breakfast.value.trim(),
        lunch: fields.lunch.value.trim(),
        snacks: fields.snacks.value.trim(),
        dinner: fields.dinner.value.trim(),
      };
  
      try {
        const response = await fetch("/analyze", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
  
        const data = await response.json();
  
        if (!response.ok) {
          const msg = data && data.error ? data.error : "Analysis failed.";
          setStatus(msg, true);
          return;
        }
  
        // Update totals
        Object.entries(resultFields).forEach(([key, el]) => {
          const value = data[key];
          if (typeof value === "number") {
            el.textContent = value.toFixed(2);
          } else if (value != null) {
            el.textContent = value;
          } else {
            el.textContent = "-";
          }
        });
  
        resultsSection.classList.remove("hidden");
  
        // Handle unmatched items
        const unmatched = Array.isArray(data.unmatched_items)
          ? data.unmatched_items
          : [];
  
        if (unmatched.length > 0) {
          unmatchedList.innerHTML = "";
          unmatched.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            unmatchedList.appendChild(li);
          });
          unmatchedSection.classList.remove("hidden");
        } else {
          unmatchedSection.classList.add("hidden");
        }
  
        setStatus("Analysis complete.");
      } catch (err) {
        console.error(err);
        setStatus("Unexpected error while contacting the server.", true);
      }
    }
  
    analyzeBtn.addEventListener("click", () => {
      analyzeMeals();
    });
  });