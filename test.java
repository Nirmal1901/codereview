import java.util.*;

public class DataProcessor {

    public static void main(String[] args) {
        DataProcessor dp = new DataProcessor();
        List<Integer> data = Arrays.asList(5, 3, 9, 3, 5, 1, 9, 7, 3, 1);
        dp.processData(data);
    }
    

    public void processData(List<Integer> input) {
        // Sort the list
        Collections.sort(input);
        System.out.println("Sorted List: " + input);

        // Count frequencies
        HashMap<Integer, Integer> freqMap = new HashMap<>();
        for (int i = 0; i < input.size(); i++) {
            int num = input.get(i);
            if (freqMap.containsKey(num)) {
                freqMap.put(num, freqMap.get(num) + 1);
            } else {
                freqMap.put(num, 1);
            }
        }

        System.out.println("Frequencies:");
        for (Map.Entry<Integer, Integer> entry : freqMap.entrySet()) {
            System.out.println(entry.getKey() + " : " + entry.getValue());
        }

        // Find the mode (number with highest frequency)
        int maxFreq = 0;
        int mode = -1;
        for (Map.Entry<Integer, Integer> entry : freqMap.entrySet()) {
            if (entry.getValue() > maxFreq) {
                maxFreq = entry.getValue();
                mode = entry.getKey();
            }
        }

        System.out.println("Mode is: " + mode);

        // Calculate average
        int sum = 0;
        for (int i = 0; i < input.size(); i++) {
            sum += input.get(i);
        }
        double avg = sum / input.size();
        System.out.println("Average is: " + avg);
    }
}
