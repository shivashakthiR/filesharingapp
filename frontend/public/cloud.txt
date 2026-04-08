import org.cloudbus.cloudsim.*;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.provisioners.BwProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.PeProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import java.util.*;

public class FCFS_Example {
    public static void main(String[] args) {
        try {
            // Step 1: Initialize CloudSim
            int numUser = 1;
            Calendar calendar = Calendar.getInstance();
            CloudSim.init(numUser, calendar, false);

            // Step 2: Create Datacenter
            Datacenter datacenter0 = createDatacenter("Datacenter_0");

            // Step 3: Create Broker
            DatacenterBroker broker = new DatacenterBroker("Broker");
            int brokerId = broker.getId();

            // Step 4: Create VM with SpaceShared Scheduler (Acts as FCFS)
            List<Vm> vmlist = new ArrayList<>();
            Vm vm = new Vm(0, brokerId, 1000, 1, 512, 1000, 10000, "Xen", new CloudletSchedulerSpaceShared());
            vmlist.add(vm);
            broker.submitVmList(vmlist);

            // Step 5: Create Cloudlets (Tasks)
            List<Cloudlet> cloudletList = new ArrayList<>();
            UtilizationModel model = new UtilizationModelFull();
            
            // Task 1: Long task, Task 2: Short task
            Cloudlet c1 = new Cloudlet(0, 40000, 1, 300, 300, model, model, model);
            c1.setUserId(brokerId);
            Cloudlet c2 = new Cloudlet(1, 10000, 1, 300, 300, model, model, model);
            c2.setUserId(brokerId);

            cloudletList.add(c1);
            cloudletList.add(c2);
            broker.submitCloudletList(cloudletList);

            // Step 6: Start Simulation
            CloudSim.startSimulation();
            List<Cloudlet> newList = broker.getCloudletReceivedList();
            CloudSim.stopSimulation();

            // Print Results
            printCloudletList(newList);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static Datacenter createDatacenter(String name) {
        List<Host> hostList = new ArrayList<>();
        List<Pe> peList = new ArrayList<>();
        peList.add(new Pe(0, new PeProvisionerSimple(1000))); 
        hostList.add(new Host(0, new RamProvisionerSimple(2048), new BwProvisionerSimple(10000), 1000000, peList, new VmSchedulerTimeShared(peList)));
        
        DatacenterCharacteristics characteristics = new DatacenterCharacteristics("x86", "Linux", "Xen", hostList, 10.0, 3.0, 0.05, 0.1, 0.1);
        try {
            return new Datacenter(name, characteristics, new VmAllocationPolicySimple(hostList), new LinkedList<>(), 0);
        } catch (Exception e) { return null; }
    }

    private static void printCloudletList(List<Cloudlet> list) {
        System.out.println("Cloudlet ID | Status | Finish Time");
        for (Cloudlet c : list) {
            System.out.println(c.getCloudletId() + " | SUCCESS | " + c.getFinishTime());
        }
    }
}

