import React from 'react';
import MainHeadline from '../../components/typography/MainHeadline';
import DefaultParagraph from '../../components/typography/DefaultParagraph';
import SubHeadline from '../../components/typography/SubHeadline';

const Home: React.FC = () => {
  return (
    <>
      <div className='container mx-auto p-4'>
        <MainHeadline text='Welcome' />
        <DefaultParagraph
          text='Easytopics is your all-in-one solution for seamlessly extracting insights from your text documents.
          With our user-friendly web app, you can transform scattered texts into valuable clusters of information,
          all at your fingertips.'
        />
        <SubHeadline text='How Does It Work?' />
      </div>
    </>
  );
};

export default Home;
