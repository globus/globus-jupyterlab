import { isEndpointId, convertBytes } from './utils';
import { expect } from 'chai';
import 'mocha';

describe('Endpoint ID Validation function', () => {

    it('should return true (boolean)', () => {
        const result = isEndpointId('21498f95-b107-4c9a-a9c3-7bcc2183445f');
        expect(result).to.equal(true);
    });

    it('1st case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f950d-b107-4c9a-a9c3-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('2nd case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-4b107-4c9a-a9c3-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('3rd case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-4107-4c96a-a9c3-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('4th case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-4107-4c6a-10963-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('5th case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-4107-4c96a-a9c3-78bcc2183445f');
        expect(result).to.equal(false);
    });

    it('6th case for incorrect (id) structure, should return false (boolean)', () => {
        const result = isEndpointId('21498f954a074c96aa9c37bcc2183445f');
        expect(result).to.equal(false);
    });

    it('1st case for invalid characters in id, should return false (boolean)', () => {
        const result = isEndpointId('2149#f95-b107-4c9a-a9c3-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('2nd case for invalid characters in id, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-b107-4c9a-a:c3-7bcc2183445f');
        expect(result).to.equal(false);
    });

    it('3rd case for invalid characters in id, should return false (boolean)', () => {
        const result = isEndpointId('21498f95-b107-4c9a-a9c3-7bcc2183"45f');
        expect(result).to.equal(false);
    });

});

describe('Byte Conversion', () => {

    it('should return 0 B (string) when given null value', () => {
        const result = convertBytes(null);
        expect(result).to.equal("0 B");
    });

    it('1st case for valid input', () => {
        const result = convertBytes(1699325);
        expect(result).to.equal("1.7 MB");
    });

    it('2nd case for valid input', () => {
        const result = convertBytes(369);
        expect(result).to.equal("369 B");
    });

    it('3rd case for valid input', () => {
        const result = convertBytes(1056);
        expect(result).to.equal("1.06 KB");
    });

    it('4th case for valid input', () => {
        const result = convertBytes(580926);
        expect(result).to.equal("580.93 KB");
    });

    it('5th case for valid input', () => {
        const result = convertBytes(33092604651);
        expect(result).to.equal("33.09 GB");
    });

    it('6th case for valid input', () => {
        const result = convertBytes(6705201348306090);
        expect(result).to.equal("6705.20 TB");
    });

});