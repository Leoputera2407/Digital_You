import { ReactNode } from "react";
import {
  GiArtificialIntelligence,
  GiBrain,
  GiDatabase,
  GiFastArrow,
  GiLockedDoor,
  GiOpenBook
} from "react-icons/gi";

import Card from "../lib/Card";

const Features_new = (): JSX.Element => {
  return (
    <section className="my-20 text-center flex flex-col items-center justify-center gap-10">
      
      <div>
        <h1 className="text-5xl font-bold ">Features</h1>
        {/* <h2 className="opacity-50">Change the way you take notes</h2> */}
      </div>
      <div className="flex flex-wrap gap-5 justify-center">
        <Feature
          icon={<GiBrain className="text-7xl w-full" />}
          title="Time Saver"
          desc="Prosona dramatically reduces the time spent on answering queries, increasing productivity and balance in the workplace."
        />
        <Feature
          icon={<GiDatabase className="text-7xl w-full" />}
          title="Accountability Assurance"
          desc="With oversight by the expert before the message is sent, there is clear accountability and the risk of outdated or incorrect information being spread is mitigated."
        />
        <Feature
          icon={<GiArtificialIntelligence className="text-7xl w-full" />}
          title="Handles Diverse Internal Documents"
          desc="Prosona can manage a wide range of internal documentation, utilizing them to draft responses to queries in the tone of the expert."
        />
        <Feature
          icon={<GiFastArrow className="text-7xl w-full" />}
          title="Answerer-Centric Approach"
          desc="Prosona champions an answerer-centric view, respecting the human tendency to seek information from reliable, upstream sources."
        />
        <Feature
          icon={<GiLockedDoor className="text-7xl w-full" />}
          title="Incentivizes Documentation"
          desc="Prosona promotes comprehensive documentation and data recording, enhancing the robustness of the company's knowledge base."
        />
        <Feature
          icon={<GiOpenBook className="text-7xl w-full" />}
          title="Knowledge Condenser"
          desc="Prosona acts as a sophisticated knowledge compressor, distilling your experts' vast knowledge into digestible responses to queries."
        />
      </div>
    </section>
  );
};

interface FeatureProps {
  icon?: ReactNode;
  title: string;
  desc: string;
}

const Feature = ({ title, desc, icon }: FeatureProps): JSX.Element => {
  return (
    <Card className="p-10 max-w-xs flex flex-col gap-5 w-full">
      {icon}
      <h1 className="text-xl font-bold">{title}</h1>
      <p>{desc}</p>
    </Card>
  );
};

export default Features_new;
